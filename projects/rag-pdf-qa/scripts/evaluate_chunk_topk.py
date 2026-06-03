import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.embedding_client import embed_text
from app.pdf_extractor import extract_text_from_pdf_bytes
from app.text_splitter import split_pdf_text
from app.vector_store import ensure_collection, get_qdrant_client, search_chunks, upsert_chunks


CHUNK_CONFIGS = [
    {"chunk_size": 500, "overlap": 80},
    {"chunk_size": 800, "overlap": 100},
    {"chunk_size": 1000, "overlap": 150},
]
TOP_K_VALUES = [3, 5]
LOW_SCORE_THRESHOLD = 0.45
PREFERRED_CHUNK_SIZE = 800
PREFERRED_OVERLAP = 100


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate chunk_size, overlap, and top_k for local RAG search.")
    parser.add_argument("--cases", default="data/eval/rag_eval_cases.json")
    parser.add_argument("--output-json", default="data/eval/chunk_topk_eval_result.json")
    parser.add_argument("--output-md", default="data/eval/chunk_topk_eval_result.md")
    parser.add_argument("--source-file", default=None)
    parser.add_argument("--qdrant-dir", default=".qdrant_eval")
    args = parser.parse_args()

    cases_path = Path(args.cases)
    dataset = _read_json(cases_path)
    source_file = Path(args.source_file or dataset["source_file"])
    if not source_file.exists():
        raise FileNotFoundError(f"Source file does not exist: {source_file}")

    settings = get_settings()
    content = source_file.read_bytes()
    extracted = extract_text_from_pdf_bytes(filename=source_file.name, content=content)
    scored_cases = [case for case in dataset["cases"] if case.get("question_type") != "insufficient_context"]

    qdrant_dir = Path(args.qdrant_dir)
    _reset_eval_dir(qdrant_dir)

    results = []
    for chunk_config in CHUNK_CONFIGS:
        chunks = split_pdf_text(
            extracted,
            chunk_size=chunk_config["chunk_size"],
            overlap=chunk_config["overlap"],
        )
        vectors = [embed_text(chunk.text, settings.embedding_model) for chunk in chunks]
        dimension = len(vectors[0])
        collection_name = f"eval_chunk_{chunk_config['chunk_size']}_overlap_{chunk_config['overlap']}"
        client = get_qdrant_client(str(qdrant_dir / collection_name))
        ensure_collection(client, collection_name, dimension)
        upsert_chunks(
            client=client,
            collection_name=collection_name,
            filename=source_file.name,
            chunks=chunks,
            vectors=vectors,
            document_id=collection_name,
        )

        for top_k in TOP_K_VALUES:
            records = [
                _evaluate_case(
                    case=case,
                    client=client,
                    collection_name=collection_name,
                    embedding_model=settings.embedding_model,
                    top_k=top_k,
                )
                for case in scored_cases
            ]
            results.append(
                _summarize_records(
                    chunk_config=chunk_config,
                    top_k=top_k,
                    chunk_count=len(chunks),
                    records=records,
                )
            )

    best = max(results, key=_ranking_key)
    output = {
        "dataset_name": dataset["dataset_name"],
        "dataset_version": dataset["version"],
        "source_file": str(source_file),
        "embedding_model": settings.embedding_model,
        "low_score_threshold": LOW_SCORE_THRESHOLD,
        "scored_case_count": len(scored_cases),
        "recommendation": {
            "chunk_size": best["chunk_size"],
            "overlap": best["overlap"],
            "top_k": best["top_k"],
            "reason": (
                "Prefer the best hit metrics first. If metrics tie, keep the current default "
                "chunk_size/overlap because it preserves more context than smaller chunks."
            ),
        },
        "results": results,
    }

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(_render_markdown(output), encoding="utf-8")


def _evaluate_case(
    *,
    case: dict,
    client,
    collection_name: str,
    embedding_model: str,
    top_k: int,
) -> dict:
    query_vector = embed_text(case["question"], embedding_model)
    results = search_chunks(
        client=client,
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
    )
    expected_pages = set(case.get("expected_pages", []))
    expected_keywords = case.get("expected_keywords", [])
    all_text = "\n".join(result.text for result in results)
    matched_keywords = [keyword for keyword in expected_keywords if keyword in all_text]
    top_pages = [result.page_number for result in results]
    scores = [result.score for result in results]
    hit_by_page = bool(expected_pages.intersection(top_pages))
    hit_by_keyword = bool(matched_keywords)

    return {
        "case_id": case["case_id"],
        "question": case["question"],
        "hit": hit_by_page or hit_by_keyword,
        "hit_by_page": hit_by_page,
        "hit_by_keyword": hit_by_keyword,
        "matched_keywords": matched_keywords,
        "expected_pages": sorted(expected_pages),
        "top_pages": top_pages,
        "top_scores": scores,
        "low_score_count": sum(1 for score in scores if score < LOW_SCORE_THRESHOLD),
    }


def _summarize_records(*, chunk_config: dict, top_k: int, chunk_count: int, records: list[dict]) -> dict:
    case_count = len(records)
    low_score_count = sum(record["low_score_count"] for record in records)
    stable_hit_count = sum(1 for record in records if record["hit"])
    return {
        "chunk_size": chunk_config["chunk_size"],
        "overlap": chunk_config["overlap"],
        "top_k": top_k,
        "chunk_count": chunk_count,
        "case_count": case_count,
        "hit_count": stable_hit_count,
        "hit_rate": round(stable_hit_count / case_count, 4),
        "page_hit_count": sum(1 for record in records if record["hit_by_page"]),
        "page_hit_rate": round(sum(1 for record in records if record["hit_by_page"]) / case_count, 4),
        "keyword_hit_count": sum(1 for record in records if record["hit_by_keyword"]),
        "keyword_hit_rate": round(sum(1 for record in records if record["hit_by_keyword"]) / case_count, 4),
        "low_score_result_count": low_score_count,
        "answer_stability_note": _answer_stability_note(stable_hit_count, case_count, low_score_count),
        "records": records,
    }


def _answer_stability_note(hit_count: int, case_count: int, low_score_count: int) -> str:
    if hit_count == case_count and low_score_count == 0:
        return "检索依据稳定，适合作为 RAG 回答输入。"
    if hit_count >= case_count - 1:
        return "检索依据基本稳定，少量问题需要人工复核。"
    return "检索依据波动较大，RAG 回答容易随参数变化。"


def _ranking_key(item: dict) -> tuple[float, float, int, int, int]:
    distance_from_default = abs(item["chunk_size"] - PREFERRED_CHUNK_SIZE) + abs(item["overlap"] - PREFERRED_OVERLAP)
    return (
        item["hit_rate"],
        item["page_hit_rate"],
        -item["low_score_result_count"],
        -distance_from_default,
        item["top_k"],
    )


def _render_markdown(output: dict) -> str:
    lines = [
        "# chunk / top_k 参数评估结果",
        "",
        f"- 数据集：{output['dataset_name']} {output['dataset_version']}",
        f"- 来源文件：{output['source_file']}",
        f"- embedding：{output['embedding_model']}",
        f"- 低分噪声阈值：score < {output['low_score_threshold']}",
        f"- 推荐参数：chunk_size={output['recommendation']['chunk_size']}，"
        f"overlap={output['recommendation']['overlap']}，top_k={output['recommendation']['top_k']}",
        "",
        "| chunk_size | overlap | top_k | chunk_count | hit_rate | page_hit_rate | keyword_hit_rate | low_score_count | 稳定性 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in output["results"]:
        lines.append(
            "| {chunk_size} | {overlap} | {top_k} | {chunk_count} | {hit_rate:.4f} | "
            "{page_hit_rate:.4f} | {keyword_hit_rate:.4f} | {low_score_result_count} | {answer_stability_note} |".format(
                **result
            )
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "本评估只调用本地 embedding 和本地 Qdrant，不调用 DeepSeek。",
            "回答稳定性是基于检索命中稳定性推断的前置指标。",
        ]
    )
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _reset_eval_dir(path: Path) -> None:
    if path.exists():
        resolved = path.resolve()
        project_root = Path.cwd().resolve()
        if not str(resolved).startswith(str(project_root)):
            raise RuntimeError(f"Refuse to delete eval directory outside project: {resolved}")
        shutil.rmtree(resolved)
    path.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
