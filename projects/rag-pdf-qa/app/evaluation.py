from dataclasses import dataclass
from datetime import UTC, datetime, timezone
import json
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.db import session_scope
from app.embedding_client import embed_text
from app.models import EvaluationCaseModel, EvaluationRunModel
from app.vector_store import get_qdrant_client, search_chunks


DEFAULT_EVALUATION_DATASET_PATH = Path("data/eval/rag_eval_cases.json")
DEFAULT_EVALUATION_RESULT_PATH = Path("data/eval/latest_rag_evaluation.json")
DEFAULT_EVALUATION_REPORT_PATH = Path("data/eval/latest_rag_evaluation.md")
LOW_SCORE_THRESHOLD = 0.45


class EvaluationError(RuntimeError):
    pass


@dataclass(frozen=True)
class EvaluationRunSummary:
    run_id: str
    generated_at: str
    dataset_name: str
    dataset_version: str
    knowledge_base_id: str | None
    collection: str
    embedding_model: str
    llm_provider: str | None
    llm_model: str | None
    limit: int
    score_threshold: float | None
    hit_rate: float
    page_hit_rate: float
    keyword_hit_rate: float
    quality_status: str


class EvaluationStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def sync_cases(self, *, dataset: dict[str, Any], knowledge_base_id: str | None) -> None:
        dataset_name = str(dataset.get("dataset_name", "rag_eval"))
        dataset_version = str(dataset.get("version", ""))
        now = datetime.now(UTC).isoformat()
        try:
            with session_scope(self.database_url) as session:
                for case in dataset.get("cases", []):
                    case_id = str(case.get("case_id", ""))
                    evaluation_case_id = _evaluation_case_id(
                        dataset_name=dataset_name,
                        dataset_version=dataset_version,
                        knowledge_base_id=knowledge_base_id,
                        case_id=case_id,
                    )
                    existing = session.get(EvaluationCaseModel, evaluation_case_id)
                    expected = {
                        "expected_pages": case.get("expected_pages", []),
                        "expected_keywords": case.get("expected_keywords", []),
                        "expected_source_hint": case.get("expected_source_hint", ""),
                        "notes": case.get("notes", ""),
                    }
                    if existing:
                        existing.question = str(case.get("question", ""))
                        existing.question_type = str(case.get("question_type", ""))
                        existing.expected_json = json.dumps(expected, ensure_ascii=False)
                        existing.updated_at = now
                        continue
                    session.add(
                        EvaluationCaseModel(
                            evaluation_case_id=evaluation_case_id,
                            dataset_name=dataset_name,
                            dataset_version=dataset_version,
                            knowledge_base_id=knowledge_base_id,
                            case_id=case_id,
                            question=str(case.get("question", "")),
                            question_type=str(case.get("question_type", "")),
                            expected_json=json.dumps(expected, ensure_ascii=False),
                            created_at=now,
                            updated_at=now,
                        )
                    )
        except SQLAlchemyError as exc:
            raise EvaluationError(f"Failed to persist evaluation cases: {exc}") from exc

    def save_run(self, result: dict[str, Any]) -> None:
        try:
            with session_scope(self.database_url) as session:
                session.add(
                    EvaluationRunModel(
                        run_id=result["run_id"],
                        generated_at=result["generated_at"],
                        dataset_name=result["dataset_name"],
                        dataset_version=result.get("dataset_version", ""),
                        knowledge_base_id=result.get("knowledge_base_id"),
                        collection=result["collection"],
                        embedding_model=result["embedding_model"],
                        llm_provider=result.get("llm_provider"),
                        llm_model=result.get("llm_model"),
                        limit=int(result["limit"]),
                        score_threshold=_score_threshold_text(result.get("score_threshold")),
                        hit_rate=str(result["hit_rate"]),
                        page_hit_rate=str(result["page_hit_rate"]),
                        keyword_hit_rate=str(result["keyword_hit_rate"]),
                        quality_status=str(result.get("quality_gate", {}).get("status", "unknown")),
                        result_json=json.dumps(result, ensure_ascii=False),
                    )
                )
        except SQLAlchemyError as exc:
            raise EvaluationError(f"Failed to persist evaluation run: {exc}") from exc

    def list_runs(self, *, knowledge_base_id: str | None = None, limit: int = 20) -> list[EvaluationRunSummary]:
        try:
            with session_scope(self.database_url) as session:
                statement = select(EvaluationRunModel)
                if knowledge_base_id:
                    statement = statement.where(EvaluationRunModel.knowledge_base_id == knowledge_base_id)
                rows = session.scalars(
                    statement.order_by(EvaluationRunModel.generated_at.desc()).limit(limit)
                ).all()
                return [_summary_from_run(row) for row in rows]
        except SQLAlchemyError as exc:
            raise EvaluationError(f"Failed to list evaluation runs: {exc}") from exc

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        try:
            with session_scope(self.database_url) as session:
                row = session.get(EvaluationRunModel, run_id)
                return json.loads(row.result_json) if row else None
        except SQLAlchemyError as exc:
            raise EvaluationError(f"Failed to get evaluation run: {exc}") from exc


def load_evaluation_dataset(path: Path = DEFAULT_EVALUATION_DATASET_PATH) -> dict[str, Any]:
    if not path.exists():
        raise EvaluationError(f"Evaluation dataset not found: {path}")

    try:
        dataset = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise EvaluationError(f"Failed to read evaluation dataset: {exc}") from exc

    if not isinstance(dataset.get("cases"), list):
        raise EvaluationError("Evaluation dataset must contain a cases list")
    return dataset


def run_rag_search_evaluation(
    *,
    settings: Any,
    dataset_path: Path = DEFAULT_EVALUATION_DATASET_PATH,
    output_json_path: Path = DEFAULT_EVALUATION_RESULT_PATH,
    output_md_path: Path = DEFAULT_EVALUATION_REPORT_PATH,
    limit: int = 5,
    score_threshold: float | None = None,
    knowledge_base_id: str | None = None,
) -> dict[str, Any]:
    dataset = load_evaluation_dataset(dataset_path)
    client = get_qdrant_client(
        settings.qdrant_local_path,
        mode=getattr(settings, "qdrant_mode", "local"),
        url=getattr(settings, "qdrant_url", "http://127.0.0.1:6333"),
        api_key=getattr(settings, "qdrant_api_key", ""),
    )

    case_results = []
    for case in dataset["cases"]:
        case_results.append(
            _evaluate_case(
                case=case,
                client=client,
                collection_name=settings.qdrant_collection,
                embedding_model=settings.embedding_model,
                limit=limit,
                score_threshold=score_threshold,
                knowledge_base_id=knowledge_base_id,
            )
        )

    summary = _summarize_results(case_results)
    quality_gate = _build_quality_gate(summary)
    result = {
        "run_id": f"eval_{uuid4().hex[:16]}",
        "dataset_name": dataset.get("dataset_name", "rag_eval"),
        "dataset_version": dataset.get("version", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collection": settings.qdrant_collection,
        "embedding_model": settings.embedding_model,
        "llm_provider": getattr(settings, "llm_provider", None),
        "llm_model": getattr(settings, "llm_model", None),
        "limit": limit,
        "score_threshold": score_threshold,
        "knowledge_base_id": knowledge_base_id,
        "low_score_threshold": LOW_SCORE_THRESHOLD,
        "quality_gate": quality_gate,
        **summary,
        "cases": case_results,
    }

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md_path.write_text(render_evaluation_markdown(result), encoding="utf-8")
    database_url = getattr(settings, "database_url", None)
    if database_url:
        store = EvaluationStore(database_url)
        store.sync_cases(dataset=dataset, knowledge_base_id=knowledge_base_id)
        store.save_run(result)
    return result


def list_evaluation_runs(
    *,
    settings: Any,
    knowledge_base_id: str | None = None,
    limit: int = 20,
) -> list[EvaluationRunSummary]:
    database_url = getattr(settings, "database_url", None)
    if not database_url:
        raise EvaluationError("DATABASE_URL is required to list evaluation runs")
    return EvaluationStore(database_url).list_runs(knowledge_base_id=knowledge_base_id, limit=limit)


def read_evaluation_run(*, settings: Any, run_id: str) -> dict[str, Any]:
    database_url = getattr(settings, "database_url", None)
    if not database_url:
        raise EvaluationError("DATABASE_URL is required to read evaluation runs")
    result = EvaluationStore(database_url).get_run(run_id)
    if result is None:
        raise EvaluationError(f"Evaluation run not found: {run_id}")
    return result


def read_latest_evaluation(path: Path = DEFAULT_EVALUATION_RESULT_PATH) -> dict[str, Any]:
    if not path.exists():
        raise EvaluationError(f"Latest evaluation result not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise EvaluationError(f"Failed to read latest evaluation result: {exc}") from exc


def render_evaluation_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# RAG 检索评估结果",
        "",
        f"- 数据集：{result['dataset_name']} {result.get('dataset_version', '')}",
        f"- 生成时间：{result['generated_at']}",
        f"- collection：{result['collection']}",
        f"- embedding：{result['embedding_model']}",
        f"- top_k：{result['limit']}",
        f"- score_threshold：{result['score_threshold']}",
        f"- hit_rate：{result['hit_rate']:.4f}",
        f"- page_hit_rate：{result['page_hit_rate']:.4f}",
        f"- keyword_hit_rate：{result['keyword_hit_rate']:.4f}",
        "",
        "| case | hit | page_hit | keyword_hit | top_scores | question |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in result["cases"]:
        lines.append(
            "| {case_id} | {hit} | {page_hit} | {keyword_hit} | {scores} | {question} |".format(
                case_id=item["case_id"],
                hit="yes" if item["hit"] else "no",
                page_hit="yes" if item["page_hit"] else "no",
                keyword_hit="yes" if item["keyword_hit"] else "no",
                scores=", ".join(f"{score:.4f}" for score in item["top_scores"]),
                question=item["question"].replace("|", "/"),
            )
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "本评估只调用本地 embedding 和本地 Qdrant，不调用 DeepSeek。",
        ]
    )
    return "\n".join(lines) + "\n"


def _evaluate_case(
    *,
    case: dict[str, Any],
    client: Any,
    collection_name: str,
    embedding_model: str,
    limit: int,
    score_threshold: float | None,
    knowledge_base_id: str | None,
) -> dict[str, Any]:
    query_vector = embed_text(case["question"], embedding_model)
    raw_results = search_chunks(
        client=client,
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        knowledge_base_id=knowledge_base_id,
    )
    results = [
        result
        for result in raw_results
        if score_threshold is None or result.score >= score_threshold
    ]
    expected_pages = set(case.get("expected_pages", []))
    expected_keywords = case.get("expected_keywords", [])
    all_text = "\n".join(result.text for result in results)
    matched_keywords = [keyword for keyword in expected_keywords if keyword in all_text]
    top_pages = [result.page_number for result in results]
    top_scores = [float(result.score) for result in results]
    page_hit = bool(expected_pages.intersection(top_pages))
    keyword_hit = bool(matched_keywords)
    scored = bool(expected_pages or expected_keywords)

    return {
        "case_id": case.get("case_id", ""),
        "question": case["question"],
        "question_type": case.get("question_type", ""),
        "scored": scored,
        "hit": scored and (page_hit or keyword_hit),
        "page_hit": page_hit,
        "keyword_hit": keyword_hit,
        "expected_pages": sorted(expected_pages),
        "matched_keywords": matched_keywords,
        "top_pages": top_pages,
        "top_scores": top_scores,
        "top_sources": [
            {
                "score": float(result.score),
                "document_id": result.document_id,
                "file_type": result.file_type,
                "filename": result.filename,
                "page_number": result.page_number,
                "chunk_id": result.chunk_id,
                "extraction_method": result.extraction_method,
                "preview": " ".join(result.text.split())[:180],
            }
            for result in results
        ],
        "low_score_count": sum(1 for result in raw_results if result.score < LOW_SCORE_THRESHOLD),
    }


def _summarize_results(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    scored_cases = [item for item in case_results if item["scored"]]
    scored_count = len(scored_cases)
    hit_count = sum(1 for item in scored_cases if item["hit"])
    page_hit_count = sum(1 for item in scored_cases if item["page_hit"])
    keyword_hit_count = sum(1 for item in scored_cases if item["keyword_hit"])

    return {
        "case_count": len(case_results),
        "scored_case_count": scored_count,
        "hit_count": hit_count,
        "hit_rate": round(hit_count / scored_count, 4) if scored_count else 0,
        "page_hit_count": page_hit_count,
        "page_hit_rate": round(page_hit_count / scored_count, 4) if scored_count else 0,
        "keyword_hit_count": keyword_hit_count,
        "keyword_hit_rate": round(keyword_hit_count / scored_count, 4) if scored_count else 0,
        "low_score_result_count": sum(item["low_score_count"] for item in case_results),
    }


def _build_quality_gate(summary: dict[str, Any]) -> dict[str, Any]:
    thresholds = {
        "min_hit_rate": 0.6,
        "min_page_hit_rate": 0.5,
        "max_low_score_result_count": 10,
    }
    failures = []
    if summary["hit_rate"] < thresholds["min_hit_rate"]:
        failures.append("hit_rate")
    if summary["page_hit_rate"] < thresholds["min_page_hit_rate"]:
        failures.append("page_hit_rate")
    if summary["low_score_result_count"] > thresholds["max_low_score_result_count"]:
        failures.append("low_score_result_count")
    return {
        "status": "pass" if not failures else "fail",
        "thresholds": thresholds,
        "failures": failures,
        "judge_reserved": True,
    }


def _evaluation_case_id(
    *,
    dataset_name: str,
    dataset_version: str,
    knowledge_base_id: str | None,
    case_id: str,
) -> str:
    seed = f"{dataset_name}:{dataset_version}:{knowledge_base_id or 'global'}:{case_id}"
    return f"eval_case_{uuid5(NAMESPACE_URL, seed).hex[:24]}"


def _summary_from_run(row: EvaluationRunModel) -> EvaluationRunSummary:
    return EvaluationRunSummary(
        run_id=row.run_id,
        generated_at=row.generated_at,
        dataset_name=row.dataset_name,
        dataset_version=row.dataset_version,
        knowledge_base_id=row.knowledge_base_id,
        collection=row.collection,
        embedding_model=row.embedding_model,
        llm_provider=row.llm_provider,
        llm_model=row.llm_model,
        limit=row.limit,
        score_threshold=float(row.score_threshold) if row.score_threshold not in (None, "") else None,
        hit_rate=float(row.hit_rate),
        page_hit_rate=float(row.page_hit_rate),
        keyword_hit_rate=float(row.keyword_hit_rate),
        quality_status=row.quality_status,
    )


def _score_threshold_text(value: object) -> str | None:
    return None if value is None else str(value)
