import json
from types import SimpleNamespace

from app import evaluation
from app.vector_store import SearchResult


def test_load_evaluation_dataset_requires_cases_list(tmp_path):
    dataset_path = tmp_path / "bad_eval.json"
    dataset_path.write_text(json.dumps({"dataset_name": "bad"}), encoding="utf-8")

    try:
        evaluation.load_evaluation_dataset(dataset_path)
    except evaluation.EvaluationError as exc:
        assert "cases list" in str(exc)
    else:
        raise AssertionError("dataset without cases should raise EvaluationError")


def test_run_rag_search_evaluation_saves_json_and_markdown(tmp_path, monkeypatch):
    dataset_path = tmp_path / "rag_eval_cases.json"
    output_json_path = tmp_path / "out" / "latest.json"
    output_md_path = tmp_path / "report" / "latest.md"
    dataset_path.write_text(
        json.dumps(
            {
                "dataset_name": "demo_eval",
                "version": "0.1",
                "cases": [
                    {
                        "case_id": "Q1",
                        "question": "如何启动本地 RAG？",
                        "question_type": "process",
                        "expected_pages": [3],
                        "expected_keywords": ["启动", "FastAPI"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(evaluation, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(evaluation, "get_qdrant_client", lambda *args, **kwargs: object())

    def fake_search_chunks(client, collection_name, query_vector, limit, **kwargs):
        assert collection_name == "rag_chunks"
        assert query_vector == [0.1, 0.2, 0.3]
        assert limit == 2
        assert kwargs.get("knowledge_base_id") == "kb-default"
        return [
            SearchResult(
                point_id="point-1",
                score=0.91,
                document_id="doc-1",
                file_type="markdown",
                filename="runbook.md",
                page_number=3,
                chunk_id=1,
                text="启动 FastAPI 服务后打开 /app 页面。",
                extraction_method="text",
            ),
            SearchResult(
                point_id="point-2",
                score=0.32,
                document_id="doc-2",
                file_type="pdf",
                filename="other.pdf",
                page_number=9,
                chunk_id=4,
                text="无关内容。",
                extraction_method="pdf_ocr",
            ),
        ]

    monkeypatch.setattr(evaluation, "search_chunks", fake_search_chunks)

    result = evaluation.run_rag_search_evaluation(
        settings=SimpleNamespace(
            qdrant_local_path=str(tmp_path / ".qdrant"),
            qdrant_collection="rag_chunks",
            embedding_model="BAAI/bge-small-zh-v1.5",
        ),
        dataset_path=dataset_path,
        output_json_path=output_json_path,
        output_md_path=output_md_path,
        limit=2,
        score_threshold=0.4,
        knowledge_base_id="kb-default",
    )

    assert result["case_count"] == 1
    assert result["hit_rate"] == 1.0
    assert result["page_hit_rate"] == 1.0
    assert result["keyword_hit_rate"] == 1.0
    assert result["low_score_result_count"] == 1
    assert result["knowledge_base_id"] == "kb-default"
    assert result["cases"][0]["top_sources"][0]["filename"] == "runbook.md"
    assert result["cases"][0]["top_sources"][0]["extraction_method"] == "text"
    assert output_json_path.exists()
    assert output_md_path.exists()
    assert json.loads(output_json_path.read_text(encoding="utf-8"))["dataset_name"] == "demo_eval"
    assert "RAG 检索评估结果" in output_md_path.read_text(encoding="utf-8")
