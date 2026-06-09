from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.audit import AuditLogStore
from app.config import Settings
from app.db import session_scope
from app.document_loaders import ParsedDocument, ParsedSection
from app.document_store import DocumentRecord
from app.evaluation import EvaluationRunSummary
from app.models import AnswerQualityJudgementModel, AuditLogModel
from app.pdf_extractor import ExtractedImage, ExtractedPage, ExtractedPdf, ExtractedTable
from app.runtime_settings import RuntimeSettings
from app.text_splitter import TextChunk
from app.vector_store import SearchResult
from app.web_page_fetcher import FetchedWebPage, WebPageFetchError


def test_search_documents_returns_retrieved_results(monkeypatch):
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda *args, **kwargs: object())
    monkeypatch.setattr(main, "_require_document_in_knowledge_base", lambda **kwargs: None)

    def fake_search_chunks(
        client,
        collection_name,
        query_vector,
        limit,
        document_id=None,
        file_type=None,
        knowledge_base_id=None,
        tenant_id=None,
    ):
        assert limit == 2
        assert document_id == "doc-1"
        assert file_type == "pdf"
        assert knowledge_base_id == "kb_default"
        return [
            SearchResult(
                point_id="point-1",
                score=0.82,
                document_id="doc-1",
                file_type="pdf",
                filename="demo.pdf",
                page_number=3,
                chunk_id=7,
                text="GUI Agent follows observe, plan, act, and reflect steps.",
            )
        ]

    monkeypatch.setattr(main, "search_chunks", fake_search_chunks)

    client = TestClient(main.app)
    response = client.post(
        "/documents/search",
        json={"query": "GUI Agent flow", "limit": 2, "document_id": "doc-1", "file_type": "pdf"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "GUI Agent flow"
    assert data["limit"] == 2
    assert data["document_id"] == "doc-1"
    assert data["file_type"] == "pdf"
    assert data["results"][0]["filename"] == "demo.pdf"
    assert data["results"][0]["document_id"] == "doc-1"
    assert data["results"][0]["chunk_id"] == 7


def test_web_ui_routes_are_available():
    client = TestClient(main.app)

    app_response = client.get("/app")
    docs_response = client.get("/docs")
    openapi_response = client.get("/openapi.json")

    assert app_response.status_code == 200
    assert "Local RAG Agent | Knowledge QA" in app_response.text
    assert "/web/assets/rag-agent-icon-64.png?v=29" in app_response.text
    assert "/web/assets/rag-agent-icon-192.png?v=29" in app_response.text
    assert 'data-tab="import"' in app_response.text
    assert 'data-tab="ask"' in app_response.text
    assert 'data-tab="evaluation"' in app_response.text
    assert 'data-tab="settings"' in app_response.text
    assert 'id="tab-ask" role="tabpanel" hidden' in app_response.text
    assert 'id="tab-evaluation" role="tabpanel" hidden' in app_response.text
    assert 'id="tab-settings" role="tabpanel" hidden' in app_response.text
<<<<<<< HEAD
    assert "/web/styles.css?v=43" in app_response.text
    assert "/web/app.js?v=43" in app_response.text
=======
<<<<<<< HEAD
    assert "/web/styles.css?v=40" in app_response.text
    assert "/web/app.js?v=41" in app_response.text
=======
    assert "/web/styles.css?v=41" in app_response.text
    assert "/web/app.js?v=41" in app_response.text
>>>>>>> 54150954f5ddeeac4a794980a0eaf0e85bed9248
    assert 'id="knowledgeBaseSelect"' in app_response.text
    assert 'id="knowledgeBaseForm"' in app_response.text
    assert 'id="indexJobList"' in app_response.text
    assert 'id="refreshIndexJobs"' in app_response.text
<<<<<<< HEAD
    assert 'id="evaluationHistory"' in app_response.text
    assert 'id="reloadEvaluationRuns"' in app_response.text
=======
>>>>>>> e0d56302c3febb53fc08d3d5219d1bc8e7a1149f
>>>>>>> 54150954f5ddeeac4a794980a0eaf0e85bed9248
    assert "分块大小 chunk" in app_response.text
    assert "重叠长度 overlap" in app_response.text
    assert "重新索引 reindex" in app_response.text
    assert "检索数量 top_k" in app_response.text
    assert "分数阈值 threshold" in app_response.text
    assert "接口地址 API Base URL" in app_response.text
    assert 'data-ask-mode="rag"' in app_response.text
    assert 'data-ask-mode="agent"' in app_response.text
    assert 'id="documentNameFilter"' in app_response.text
    assert 'id="documentTypeFilter"' in app_response.text
    assert 'id="selectedDocumentCount"' in app_response.text
    assert 'id="batchDeleteDocuments"' in app_response.text
    assert 'id="askDocumentFilter"' in app_response.text
    assert 'data-language="zh"' in app_response.text
    assert 'data-language="en"' in app_response.text
    assert 'data-theme-color="teal"' in app_response.text
    assert 'id="customColorInput"' in app_response.text
    assert 'id="backgroundColorInput"' in app_response.text
    assert 'id="providerInput"' in app_response.text
    assert 'id="modelOptions"' in app_response.text
    assert 'id="fileNameDisplay"' in app_response.text
    assert 'id="chooseFileButton"' in app_response.text
    assert 'id="profileTableBody"' in app_response.text
    assert 'id="profileModal"' in app_response.text
    assert 'id="addProfileButton"' in app_response.text
    assert 'id="registerUser"' in app_response.text
    assert 'class="team-access-section"' in app_response.text
    assert 'id="reloadTeamAccess"' in app_response.text
    assert 'id="adminUsersBlock"' in app_response.text
    assert 'id="adminUserForm"' in app_response.text
    assert 'id="adminUserList"' in app_response.text
    assert 'id="memberForm"' in app_response.text
    assert 'id="memberList"' in app_response.text
    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    assert openapi_response.json()["info"]["title"] == "Local Knowledge RAG Agent"
    assert "/auth/register" in openapi_response.json()["paths"]
    assert "/admin/users" in openapi_response.json()["paths"]
    assert "/documents/index" in openapi_response.json()["paths"]
    assert "/web-pages/index" in openapi_response.json()["paths"]
    assert "/knowledge-bases/{knowledge_base_id}/web-pages/index" in openapi_response.json()["paths"]
    assert "/documents/index-jobs" in openapi_response.json()["paths"]
    assert "/documents/index-jobs/{job_id}/retry" in openapi_response.json()["paths"]
    assert "/knowledge-bases" in openapi_response.json()["paths"]
    assert "/knowledge-bases/{knowledge_base_id}/documents" in openapi_response.json()["paths"]
    assert "/knowledge-bases/{knowledge_base_id}/members" in openapi_response.json()["paths"]
    assert "/knowledge-bases/{knowledge_base_id}/members/{user_id}" in openapi_response.json()["paths"]
    assert "/knowledge-bases/{knowledge_base_id}/snapshots" in openapi_response.json()["paths"]
    assert "/knowledge-bases/{knowledge_base_id}/snapshots/{snapshot_id}" in openapi_response.json()["paths"]
    assert (
        "/knowledge-bases/{knowledge_base_id}/snapshots/{base_snapshot_id}/diff/{target_snapshot_id}"
        in openapi_response.json()["paths"]
    )
    assert "/settings/vector-store/status" in openapi_response.json()["paths"]
    assert "/audit-logs" in openapi_response.json()["paths"]
    assert "/metrics" in openapi_response.json()["paths"]
    assert "/evaluation/runs" in openapi_response.json()["paths"]
    assert "/evaluation/runs/{run_id}" in openapi_response.json()["paths"]
    assert "/feedback/answers" in openapi_response.json()["paths"]
    assert "/evaluation/questions" in openapi_response.json()["paths"]
    assert "/evaluation/latest" in openapi_response.json()["paths"]
    assert "/evaluation/run" in openapi_response.json()["paths"]
    assert "/evaluation/judge-answer" in openapi_response.json()["paths"]


def test_health_endpoint_reports_startup_checks_without_secret_values(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(
            app_env="production",
            database_url="sqlite:///:memory:",
            redis_url="redis://redis:6379/0",
            qdrant_mode="server",
            qdrant_url="http://qdrant:6333",
            llm_api_key="your_llm_api_key_here",
            app_secret_key="change-this-local-development-secret",
            secret_encryption_key="",
            max_upload_bytes=2048,
            rate_limit_enabled=True,
            rate_limit_requests=10,
            rate_limit_window_seconds=60,
            source_storage_enabled=True,
            source_storage_backend="local",
            web_fetch_enabled=True,
            web_fetch_max_bytes=4096,
            web_fetch_allow_private_hosts=False,
        ),
    )

    client = TestClient(main.app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_env"] == "production"
    assert data["database_reachable"] is True
    assert data["qdrant_url"] == "http://qdrant:6333"
    assert data["redis_configured"] is True
    assert data["secret_encryption_configured"] is False
    assert data["max_upload_bytes"] == 2048
    assert data["rate_limit_enabled"] is True
    assert data["rate_limit_requests"] == 10
    assert data["rate_limit_window_seconds"] == 60
    assert data["source_storage_enabled"] is True
    assert data["source_storage_backend"] == "local"
    assert data["web_fetch_enabled"] is True
    assert data["web_fetch_max_bytes"] == 4096
    assert data["web_fetch_allow_private_hosts"] is False
    assert "secret_encryption_key_not_configured" in data["warnings"]
    assert "change-this-local-development-secret" not in response.text
    assert "your_llm_api_key_here" not in response.text


def test_upload_endpoints_enforce_configured_file_size(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(max_upload_bytes=4, rate_limit_enabled=False),
    )

    client = TestClient(main.app)
    response = client.post(
        "/documents/extract",
        files={"file": ("oversized.pdf", b"12345", "application/pdf")},
    )

    assert response.status_code == 413
    assert "max upload size is 4 bytes" in response.json()["detail"]


def test_rate_limit_returns_429_with_retry_after(monkeypatch):
    main._rate_limit_hits.clear()
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(
            rate_limit_enabled=True,
            rate_limit_requests=2,
            rate_limit_window_seconds=60,
        ),
    )

    client = TestClient(main.app)
    assert client.get("/auth/me").status_code == 200
    assert client.get("/auth/me").status_code == 200
    response = client.get("/auth/me")

    main._rate_limit_hits.clear()
    assert response.status_code == 429
    assert response.headers["Retry-After"]
    assert response.json()["detail"] == "Rate limit exceeded"


def test_evaluation_api_endpoints_return_dataset_and_run_result(monkeypatch):
    monkeypatch.setattr(
        main,
        "load_evaluation_dataset",
        lambda: {
            "dataset_name": "demo_eval",
            "version": "0.1",
            "cases": [
                {
                    "case_id": "Q1",
                    "question": "什么是 RAG？",
                    "question_type": "concept",
                    "expected_pages": [2],
                    "expected_keywords": ["检索"],
                }
            ],
        },
    )

    fake_result = {
        "dataset_name": "demo_eval",
        "dataset_version": "0.1",
        "generated_at": "2026-06-05T00:00:00+00:00",
        "collection": "rag_chunks",
        "embedding_model": "BAAI/bge-small-zh-v1.5",
        "limit": 3,
        "score_threshold": None,
        "low_score_threshold": 0.45,
        "case_count": 1,
        "scored_case_count": 1,
        "hit_count": 1,
        "hit_rate": 1.0,
        "page_hit_count": 1,
        "page_hit_rate": 1.0,
        "keyword_hit_count": 1,
        "keyword_hit_rate": 1.0,
        "low_score_result_count": 0,
        "cases": [
            {
                "case_id": "Q1",
                "question": "什么是 RAG？",
                "question_type": "concept",
                "scored": True,
                "hit": True,
                "page_hit": True,
                "keyword_hit": True,
                "expected_pages": [2],
                "matched_keywords": ["检索"],
                "top_pages": [2],
                "top_scores": [0.82],
                "top_sources": [
                    {
                        "score": 0.82,
                        "document_id": "doc-1",
                        "file_type": "markdown",
                        "filename": "demo.md",
                        "page_number": 2,
                        "chunk_id": 1,
                        "extraction_method": "text",
                        "preview": "RAG 会先检索资料。",
                    }
                ],
                "low_score_count": 0,
            }
        ],
    }

    def fake_run_rag_search_evaluation(*, settings, limit, score_threshold, knowledge_base_id=None):
        assert settings.qdrant_collection
        assert limit == 3
        assert score_threshold is None
        assert knowledge_base_id == "kb_default"
        return fake_result

    monkeypatch.setattr(main, "run_rag_search_evaluation", fake_run_rag_search_evaluation)
    monkeypatch.setattr(main, "read_latest_evaluation", lambda: fake_result)
    monkeypatch.setattr(
        main,
        "list_evaluation_runs",
        lambda *, settings, knowledge_base_id=None, limit=20: [
            EvaluationRunSummary(
                run_id="eval_1",
                generated_at="2026-06-05T00:00:00+00:00",
                dataset_name="demo_eval",
                dataset_version="0.1",
                knowledge_base_id=knowledge_base_id,
                collection="rag_chunks",
                embedding_model="BAAI/bge-small-zh-v1.5",
                llm_provider="deepseek",
                llm_model="deepseek-v4-flash",
                limit=3,
                score_threshold=None,
                hit_rate=1.0,
                page_hit_rate=1.0,
                keyword_hit_rate=1.0,
                quality_status="pass",
            )
        ],
    )
    monkeypatch.setattr(main, "read_evaluation_run", lambda *, settings, run_id: {**fake_result, "run_id": run_id})

    client = TestClient(main.app)

    questions_response = client.get("/evaluation/questions")
    run_response = client.post("/evaluation/run", json={"limit": 3})
    latest_response = client.get("/evaluation/latest")
    runs_response = client.get("/evaluation/runs")
    run_detail_response = client.get("/evaluation/runs/eval_1")

    assert questions_response.status_code == 200
    assert questions_response.json()["case_count"] == 1
    assert questions_response.json()["questions"][0]["expected_keywords"] == ["检索"]
    assert run_response.status_code == 200
    assert run_response.json()["hit_rate"] == 1.0
    assert run_response.json()["cases"][0]["top_sources"][0]["filename"] == "demo.md"
    assert latest_response.status_code == 200
    assert latest_response.json()["dataset_name"] == "demo_eval"
    assert runs_response.status_code == 200
    assert runs_response.json()["runs"][0]["run_id"] == "eval_1"
    assert run_detail_response.status_code == 200
    assert run_detail_response.json()["run_id"] == "eval_1"


def test_pdf_extract_and_chunk_endpoints_reject_non_pdf_files():
    client = TestClient(main.app)

    extract_response = client.post(
        "/documents/extract",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    chunk_response = client.post(
        "/documents/chunk",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"chunk_size": "800", "overlap": "100"},
    )

    assert extract_response.status_code == 400
    assert "Only PDF files" in extract_response.json()["detail"]
    assert chunk_response.status_code == 400
    assert "Only PDF files" in chunk_response.json()["detail"]


def test_pdf_extract_endpoint_returns_image_ocr_preview(monkeypatch):
    def fake_extract_text_from_pdf_bytes(
        filename,
        content,
        enable_ocr=False,
        ocr_language="chi_sim+eng",
        extract_tables=False,
        enable_image_ocr=False,
    ):
        assert enable_image_ocr is True
        assert ocr_language == "eng"
        return ExtractedPdf(
            filename=filename,
            page_count=1,
            char_count=48,
            preview="Architecture overview",
            pages=[
                ExtractedPage(
                    page_number=1,
                    char_count=21,
                    preview="Architecture overview",
                    text="Architecture overview",
                    images=[
                        ExtractedImage(
                            image_number=1,
                            char_count=27,
                            preview="Gateway to Qdrant",
                            text="Gateway to Qdrant diagram",
                        )
                    ],
                )
            ],
            scanned_like=False,
            extraction_mode="text_image_ocr",
            image_ocr_count=1,
        )

    monkeypatch.setattr(main, "extract_text_from_pdf_bytes", fake_extract_text_from_pdf_bytes)

    client = TestClient(main.app)
    response = client.post(
        "/documents/extract",
        files={"file": ("diagram.pdf", b"%PDF", "application/pdf")},
        data={"enable_image_ocr": "true", "ocr_language": "eng"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["image_ocr_count"] == 1
    assert data["pages"][0]["image_ocr_count"] == 1
    assert data["pages"][0]["images"][0]["extraction_method"] == "pdf_image_ocr"
    assert data["pages"][0]["images"][0]["preview"] == "Gateway to Qdrant"


def test_pdf_chunk_endpoint_returns_image_ocr_chunks(monkeypatch):
    extracted = ExtractedPdf(
        filename="diagram.pdf",
        page_count=1,
        char_count=48,
        preview="Architecture overview",
        pages=[ExtractedPage(page_number=1, char_count=21, preview="Architecture overview", text="Architecture overview")],
        scanned_like=False,
        extraction_mode="text_image_ocr",
        image_ocr_count=1,
    )

    monkeypatch.setattr(main, "extract_text_from_pdf_bytes", lambda **kwargs: extracted)
    monkeypatch.setattr(
        main,
        "split_pdf_text",
        lambda extracted, chunk_size, overlap: [
            TextChunk(
                chunk_id=1,
                page_number=1,
                char_count=24,
                text="Gateway to Qdrant diagram",
                extraction_method="pdf_image_ocr",
            )
        ],
    )

    client = TestClient(main.app)
    response = client.post(
        "/documents/chunk",
        files={"file": ("diagram.pdf", b"%PDF", "application/pdf")},
        data={"chunk_size": "100", "overlap": "0", "enable_image_ocr": "true"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["image_ocr_count"] == 1
    assert data["chunks"][0]["extraction_method"] == "pdf_image_ocr"


def test_build_rag_messages_requires_stable_output_format():
    messages = main._build_rag_messages(
        question="GUI Agent 的核心流程是什么？",
        results=[
            SearchResult(
                point_id="point-1",
                score=0.82,
                document_id="doc-1",
                file_type="pdf",
                filename="demo.pdf",
                page_number=3,
                chunk_id=7,
                text="GUI Agent includes observe, plan, act, and reflect.",
            )
        ],
    )

    prompt_text = "\n".join(message["content"] for message in messages)

    assert "答案：" in prompt_text
    assert "依据：" in prompt_text
    assert "资料不足之处：" in prompt_text
    assert "操作步骤" in prompt_text
    assert "不要只回答一句话" in prompt_text
    assert "[Source 1]" in prompt_text


def test_build_rag_messages_accepts_runtime_prompt_override():
    messages = main._build_rag_messages(
        question="如何通过后端拉起前端？",
        results=[
            SearchResult(
                point_id="point-1",
                score=0.82,
                document_id="doc-1",
                file_type="markdown",
                filename="demo.md",
                page_number=1,
                chunk_id=1,
                text="FastAPI can mount static files and return index.html.",
            )
        ],
        runtime_settings=RuntimeSettings(
            rag_system_prompt="CUSTOM SYSTEM PROMPT",
            rag_answer_instructions="CUSTOM ANSWER INSTRUCTIONS",
        ),
    )

    assert messages[0]["content"] == "CUSTOM SYSTEM PROMPT"
    assert "CUSTOM ANSWER INSTRUCTIONS" in messages[1]["content"]


def test_settings_endpoint_returns_runtime_values_without_api_key(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="env-secret", deepseek_model="env-model"),
    )
    monkeypatch.setattr(
        main,
        "load_runtime_settings",
        lambda: RuntimeSettings(
            deepseek_base_url="https://runtime.example",
            deepseek_model="runtime-model",
            rag_system_prompt="runtime system",
            rag_answer_instructions="runtime answer",
        ),
    )

    client = TestClient(main.app)
    response = client.get("/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["deepseek_base_url"] == "https://runtime.example"
    assert data["deepseek_model"] == "runtime-model"
    assert data["llm_provider"] == "deepseek"
    assert data["llm_base_url"] == "https://runtime.example"
    assert data["llm_model"] == "runtime-model"
    assert data["api_key_configured"] is True
    assert data["api_key_source"] == "env"
    assert data["llm_api_key_configured"] is True
    assert data["llm_api_key_source"] == "env"
    assert data["active_llm_profile_id"] == "default"
    assert data["llm_profiles"][0]["profile_id"] == "default"
    assert data["llm_profiles"][0]["enabled"] is True
    assert data["llm_profiles"][0]["api_key_configured"] is True
    assert any(option["provider"] == "ollama" for option in data["available_providers"])
    assert "env-secret" not in response.text
    assert data["rag_system_prompt"] == "runtime system"


def test_vector_store_status_endpoint_does_not_return_api_key(monkeypatch):
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(
            qdrant_mode="server",
            qdrant_url="http://qdrant:6333",
            qdrant_api_key="server-secret",
            qdrant_collection_prefix="prod",
            qdrant_collection="prod_chunks",
        ),
    )
    monkeypatch.setattr(
        main,
        "_read_qdrant_collection_status",
        lambda settings: SimpleNamespace(
            exists=True,
            vector_size=384,
            points_count=3,
            status="green",
        ),
    )
    monkeypatch.setattr(main, "_read_vector_store_metadata_counts", lambda settings: (1, 3))

    client = TestClient(main.app)
    response = client.get("/settings/vector-store/status")

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "server"
    assert data["url"] == "http://qdrant:6333"
    assert data["local_path"] is None
    assert data["collection"] == "prod_chunks"
    assert data["collection_exists"] is True
    assert data["points_count"] == 3
    assert data["metadata_indexed_chunk_count"] == 3
    assert data["indexed_chunk_count_matches_metadata"] is True
    assert data["api_key_configured"] is True
    assert "server-secret" not in response.text


def test_answer_feedback_endpoint_records_user_feedback(tmp_path, monkeypatch):
    settings = Settings(database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}")
    monkeypatch.setattr(main, "get_settings", lambda: settings)

    client = TestClient(main.app)
    response = client.post(
        "/feedback/answers",
        json={
            "question": "What is RAG?",
            "answer": "RAG retrieves context before answering.",
            "rating": "up",
            "route": "rag",
            "details": {"source_count": 2},
        },
        headers={"X-Request-ID": "req-feedback-1"},
    )
    logs = AuditLogStore(settings.database_url).list_logs(limit=5)

    assert response.status_code == 200
    data = response.json()
    assert data["feedback_id"].startswith("feedback_")
    assert data["request_id"] == "req-feedback-1"
    assert data["rating"] == "up"
    assert logs[0].action == "feedback.answer"
    assert logs[0].details["rating"] == "up"


def test_answer_quality_judge_endpoint_records_structured_judgement(tmp_path, monkeypatch):
    settings = Settings(
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        llm_provider="deepseek",
        llm_api_key="judge-key",
        llm_model="judge-model",
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "load_runtime_settings", lambda: RuntimeSettings())

    class FakeJudgeClient:
        def __init__(self, effective_settings):
            assert effective_settings.llm_api_key == "judge-key"

        async def chat_messages(self, messages, max_tokens=1000, temperature=0.2):
            assert temperature == 0.0
            assert max_tokens == 800
            prompt_text = "\n".join(message["content"] for message in messages)
            assert "Question:" in prompt_text
            assert "Retrieved sources:" in prompt_text
            return {
                "reply": """```json
{
  "groundedness": 5,
  "answer_quality": 4,
  "completeness": 4,
  "risk_level": "low",
  "verdict": "pass",
  "rationale": "The answer is grounded in the supplied source."
}
```""",
                "model": "judge-model",
                "usage": {"total_tokens": 123},
            }

    monkeypatch.setattr(main, "DeepSeekClient", FakeJudgeClient)

    client = TestClient(main.app)
    response = client.post(
        "/evaluation/judge-answer",
        json={
            "question": "What is RAG?",
            "answer": "RAG retrieves relevant context before answering.",
            "route": "rag",
            "sources": [
                {
                    "source_id": 1,
                    "filename": "demo.md",
                    "page_number": 1,
                    "chunk_id": 2,
                    "preview": "RAG retrieves relevant context before answering.",
                }
            ],
        },
        headers={"X-Request-ID": "req-judge-1"},
    )
    logs = AuditLogStore(settings.database_url).list_logs(action="evaluation.judge_answer", limit=5)

    assert response.status_code == 200
    data = response.json()
    assert data["judgement_id"].startswith("judge_")
    assert data["request_id"] == "req-judge-1"
    assert data["knowledge_base_id"] == "kb_default"
    assert data["groundedness"] == 5
    assert data["answer_quality"] == 4
    assert data["completeness"] == 4
    assert data["risk_level"] == "low"
    assert data["verdict"] == "pass"
    assert data["usage"]["total_tokens"] == 123
    with session_scope(settings.database_url) as session:
        row = session.get(AnswerQualityJudgementModel, data["judgement_id"])
        assert row is not None
        assert row.verdict == "pass"
        assert row.request_id == "req-judge-1"
    assert logs[0].resource_id == data["judgement_id"]
    assert logs[0].llm_model == "judge-model"
    assert logs[0].details["verdict"] == "pass"


def test_answer_quality_judge_requires_configured_llm_key(tmp_path, monkeypatch):
    settings = Settings(database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}", llm_api_key="")
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "load_runtime_settings", lambda: RuntimeSettings())

    client = TestClient(main.app)
    response = client.post(
        "/evaluation/judge-answer",
        json={
            "question": "What is RAG?",
            "answer": "RAG retrieves context before answering.",
            "sources": [],
        },
    )
    logs = AuditLogStore(settings.database_url).list_logs(action="evaluation.judge_answer", limit=5)

    assert response.status_code == 502
    assert "LLM_API_KEY is not configured" in response.json()["detail"]
    with session_scope(settings.database_url) as session:
        assert session.scalars(select(AnswerQualityJudgementModel)).all() == []
    assert logs[0].status == "failure"
    assert logs[0].error_message == "LLM_API_KEY is not configured"


def test_update_settings_persists_runtime_values_without_returning_api_key(monkeypatch):
    saved = {}

    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="", deepseek_model="env-model"),
    )
    monkeypatch.setattr(main, "load_runtime_settings", lambda: RuntimeSettings())

    def fake_save_runtime_settings(runtime_settings):
        saved["runtime_settings"] = runtime_settings
        return runtime_settings

    monkeypatch.setattr(main, "save_runtime_settings", fake_save_runtime_settings)

    client = TestClient(main.app)
    response = client.put(
        "/settings",
        json={
            "llm_provider": "qwen",
            "llm_api_key": "runtime-secret",
            "llm_base_url": "https://runtime.example/v1",
            "llm_model": "runtime-model",
            "request_timeout_seconds": 60,
            "rag_system_prompt": "runtime system",
            "rag_answer_instructions": "runtime answer",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["api_key_configured"] is True
    assert data["api_key_source"] == "runtime"
    assert data["llm_provider"] == "qwen"
    assert data["llm_model"] == "runtime-model"
    assert data["deepseek_model"] == "runtime-model"
    assert "runtime-secret" not in response.text
    assert saved["runtime_settings"].llm_api_key == "runtime-secret"
    assert saved["runtime_settings"].llm_provider == "qwen"
    assert saved["runtime_settings"].rag_answer_instructions == "runtime answer"


def test_llm_profile_management_endpoints_do_not_return_api_key(monkeypatch):
    store = {"runtime_settings": RuntimeSettings()}

    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(llm_api_key="", llm_model="env-model"),
    )
    monkeypatch.setattr(main, "load_runtime_settings", lambda: store["runtime_settings"])

    def fake_save_runtime_settings(runtime_settings):
        store["runtime_settings"] = runtime_settings
        return runtime_settings

    monkeypatch.setattr(main, "save_runtime_settings", fake_save_runtime_settings)

    client = TestClient(main.app)
    create_response = client.post(
        "/settings/llm-profiles",
        json={
            "name": "Qwen Plus",
            "provider": "qwen",
            "api_key": "profile-secret",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus",
        },
    )

    assert create_response.status_code == 200
    create_data = create_response.json()
    assert "profile-secret" not in create_response.text
    assert len(create_data["llm_profiles"]) == 2
    qwen_profile = next(profile for profile in create_data["llm_profiles"] if profile["provider"] == "qwen")
    assert qwen_profile["api_key_configured"] is True
    assert qwen_profile["enabled"] is False

    activate_response = client.post(f"/settings/llm-profiles/{qwen_profile['profile_id']}/activate")

    assert activate_response.status_code == 200
    activate_data = activate_response.json()
    assert activate_data["active_llm_profile_id"] == qwen_profile["profile_id"]
    assert activate_data["llm_provider"] == "qwen"
    assert activate_data["llm_model"] == "qwen-plus"
    assert "profile-secret" not in activate_response.text

    delete_active_response = client.delete(f"/settings/llm-profiles/{qwen_profile['profile_id']}")
    assert delete_active_response.status_code == 400

    default_delete_response = client.delete("/settings/llm-profiles/default")
    assert default_delete_response.status_code == 200
    assert all(profile["profile_id"] != "default" for profile in default_delete_response.json()["llm_profiles"])


def test_document_management_endpoints(monkeypatch):
    record = DocumentRecord(
        document_id="doc-1",
        filename="demo.pdf",
        file_type="pdf",
        content_hash="a" * 64,
        content_hash_prefix="a" * 12,
        chunk_count=3,
        created_at="2026-06-03T00:00:00+00:00",
        indexed_at="2026-06-03T00:00:00+00:00",
        source_file_size=120,
        collection="rag_chunks",
        chunk_size=800,
        overlap=100,
        embedding_model="BAAI/bge-small-zh-v1.5",
        page_count=2,
        indexed_count=3,
    )

    class FakeDocumentStore:
        def __init__(self):
            self.records = {"doc-1": record}

        def list_documents(self, **kwargs):
            return list(self.records.values())

        def get_document(self, document_id, **kwargs):
            return self.records.get(document_id)

        def remove_document(self, document_id, **kwargs):
            return self.records.pop(document_id, None)

    fake_store = FakeDocumentStore()
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="", document_metadata_path="unused.json"),
    )
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: fake_store)
    monkeypatch.setattr(main, "get_qdrant_client", lambda *args, **kwargs: object())
    monkeypatch.setattr(main, "delete_document_chunks", lambda client, collection_name, document_id, **kwargs: 3)

    client = TestClient(main.app)

    list_response = client.get("/documents")
    assert list_response.status_code == 200
    assert list_response.json()["documents"][0]["document_id"] == "doc-1"

    get_response = client.get("/documents/doc-1")
    assert get_response.status_code == 200
    assert get_response.json()["filename"] == "demo.pdf"

    delete_response = client.delete("/documents/doc-1")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted_chunks"] == 3

    missing_response = client.get("/documents/doc-1")
    assert missing_response.status_code == 404


def test_batch_delete_documents_removes_chunks_and_metadata(monkeypatch):
    records = {
        "doc-1": DocumentRecord(
            document_id="doc-1",
            filename="one.pdf",
            file_type="pdf",
            content_hash="a" * 64,
            content_hash_prefix="a" * 12,
            chunk_count=2,
            created_at="2026-06-03T00:00:00+00:00",
            indexed_at="2026-06-03T00:00:00+00:00",
            source_file_size=120,
            collection="rag_chunks",
            chunk_size=800,
            overlap=100,
            embedding_model="BAAI/bge-small-zh-v1.5",
            page_count=1,
            indexed_count=2,
        ),
        "doc-2": DocumentRecord(
            document_id="doc-2",
            filename="two.md",
            file_type="markdown",
            content_hash="b" * 64,
            content_hash_prefix="b" * 12,
            chunk_count=1,
            created_at="2026-06-03T00:00:00+00:00",
            indexed_at="2026-06-03T00:00:00+00:00",
            source_file_size=80,
            collection="rag_chunks",
            chunk_size=800,
            overlap=100,
            embedding_model="BAAI/bge-small-zh-v1.5",
            page_count=1,
            indexed_count=1,
        ),
    }

    class FakeDocumentStore:
        def get_document(self, document_id, **kwargs):
            return records.get(document_id)

        def remove_document(self, document_id, **kwargs):
            return records.pop(document_id, None)

    deleted_ids = []
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="", document_metadata_path="unused.json"),
    )
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: FakeDocumentStore())
    monkeypatch.setattr(main, "get_qdrant_client", lambda *args, **kwargs: object())

    def fake_delete_document_chunks(client, collection_name, document_id, **kwargs):
        deleted_ids.append(document_id)
        return 2

    monkeypatch.setattr(main, "delete_document_chunks", fake_delete_document_chunks)

    client = TestClient(main.app)
    response = client.request(
        "DELETE",
        "/documents/batch",
        json={"document_ids": ["doc-1", "doc-missing", "doc-2", "doc-1"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["deleted_count"] == 2
    assert data["missing_document_ids"] == ["doc-missing"]
    assert deleted_ids == ["doc-1", "doc-2"]
    assert records == {}


def test_reindex_document_replaces_existing_document_with_uploaded_file(monkeypatch):
    existing = DocumentRecord(
        document_id="doc-1",
        filename="old.md",
        file_type="markdown",
        content_hash="a" * 64,
        content_hash_prefix="a" * 12,
        chunk_count=1,
        created_at="2026-06-03T00:00:00+00:00",
        indexed_at="2026-06-03T00:00:00+00:00",
        source_file_size=80,
        collection="rag_chunks",
        chunk_size=800,
        overlap=100,
        embedding_model="BAAI/bge-small-zh-v1.5",
        page_count=1,
        indexed_count=1,
    )

    class FakeDocumentStore:
        def __init__(self):
            self.record = existing
            self.removed_document_id = None
            self.added_kwargs = None

        def get_document(self, document_id, **kwargs):
            return self.record if document_id == "doc-1" else None

        def remove_document(self, document_id, **kwargs):
            self.removed_document_id = document_id
            self.record = None
            return existing

        def add_document(self, **kwargs):
            self.added_kwargs = kwargs
            return existing

    fake_store = FakeDocumentStore()
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="", document_metadata_path="unused.json"),
    )
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: fake_store)
    monkeypatch.setattr(
        main,
        "_parse_and_split_index_file",
        lambda **kwargs: (
            "markdown",
            1,
            [TextChunk(chunk_id=1, page_number=1, char_count=18, text="new document text")],
            None,
            0,
            0,
            ["text"],
        ),
    )
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda *args, **kwargs: object())
    monkeypatch.setattr(main, "ensure_collection", lambda client, collection_name, dimension: None)
    monkeypatch.setattr(main, "delete_document_chunks", lambda client, collection_name, document_id, **kwargs: 1)
    monkeypatch.setattr(main, "upsert_chunks", lambda **kwargs: len(kwargs["chunks"]))

    client = TestClient(main.app)
    response = client.post(
        "/documents/doc-1/reindex",
        files={"file": ("new.md", "new document text".encode("utf-8"), "text/markdown")},
        data={"chunk_size": "100", "overlap": "0"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "doc-1"
    assert data["filename"] == "new.md"
    assert data["deleted_chunks"] == 1
    assert data["indexed_count"] == 1
    assert fake_store.removed_document_id == "doc-1"
    assert fake_store.added_kwargs["document_id"] == "doc-1"
    assert fake_store.added_kwargs["filename"] == "new.md"


def test_index_document_duplicate_content_reuses_existing_record(monkeypatch):
    content = b"same pdf bytes"
    content_hash = main._calculate_content_hash(content)
    record = DocumentRecord(
        document_id="doc-duplicate",
        filename="existing.pdf",
        file_type="pdf",
        content_hash=content_hash,
        content_hash_prefix=content_hash[:12],
        chunk_count=3,
        created_at="2026-06-03T00:00:00+00:00",
        indexed_at="2026-06-03T00:00:00+00:00",
        source_file_size=len(content),
        collection="rag_chunks",
        chunk_size=800,
        overlap=100,
        embedding_model="BAAI/bge-small-zh-v1.5",
        page_count=2,
        indexed_count=3,
    )

    class FakeDocumentStore:
        def get_document_by_content_hash(self, value, **kwargs):
            assert value == content_hash
            return record

    def fail_if_called(*args, **kwargs):
        raise AssertionError("duplicate upload should not parse or index the PDF")

    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="", document_metadata_path="unused.json"),
    )
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: FakeDocumentStore())
    monkeypatch.setattr(main, "extract_text_from_pdf_bytes", fail_if_called)

    client = TestClient(main.app)
    response = client.post(
        "/documents/index",
        files={"file": ("demo.pdf", content, "application/pdf")},
        data={"chunk_size": "800", "overlap": "100"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "doc-duplicate"
    assert data["content_hash"] == content_hash
    assert data["is_duplicate"] is True
    assert data["indexed"] is False
    assert data["indexed_count"] == 0


def test_index_document_reindex_replaces_existing_chunks(monkeypatch):
    content = b"same pdf bytes"
    content_hash = main._calculate_content_hash(content)
    record = DocumentRecord(
        document_id="doc-reindex",
        filename="existing.pdf",
        file_type="pdf",
        content_hash=content_hash,
        content_hash_prefix=content_hash[:12],
        chunk_count=3,
        created_at="2026-06-03T00:00:00+00:00",
        indexed_at="2026-06-03T00:00:00+00:00",
        source_file_size=len(content),
        collection="rag_chunks",
        chunk_size=800,
        overlap=100,
        embedding_model="BAAI/bge-small-zh-v1.5",
        page_count=2,
        indexed_count=3,
    )

    class FakeDocumentStore:
        def __init__(self):
            self.removed_document_id = None
            self.added_kwargs = None

        def get_document_by_content_hash(self, value, **kwargs):
            assert value == content_hash
            return record

        def remove_document(self, document_id, **kwargs):
            self.removed_document_id = document_id
            return record

        def add_document(self, **kwargs):
            self.added_kwargs = kwargs
            return record

    fake_store = FakeDocumentStore()
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="", document_metadata_path="unused.json"),
    )
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: fake_store)
    monkeypatch.setattr(
        main,
        "extract_text_from_pdf_bytes",
        lambda filename, content, **kwargs: ExtractedPdf(
            filename=filename,
            page_count=1,
            char_count=12,
            preview="hello",
            pages=[ExtractedPage(page_number=1, char_count=12, preview="hello", text="hello world.")],
            scanned_like=False,
        ),
    )
    monkeypatch.setattr(
        main,
        "split_pdf_text",
        lambda extracted, chunk_size, overlap: [
            TextChunk(chunk_id=1, page_number=1, char_count=12, text="hello world.")
        ],
    )
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda *args, **kwargs: object())
    monkeypatch.setattr(main, "ensure_collection", lambda client, collection_name, dimension: None)
    monkeypatch.setattr(main, "delete_document_chunks", lambda client, collection_name, document_id, **kwargs: 3)
    monkeypatch.setattr(main, "upsert_chunks", lambda **kwargs: len(kwargs["chunks"]))

    client = TestClient(main.app)
    response = client.post(
        "/documents/index",
        files={"file": ("demo.pdf", content, "application/pdf")},
        data={"chunk_size": "800", "overlap": "100", "reindex": "true"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "doc-reindex"
    assert data["is_duplicate"] is False
    assert data["indexed"] is True
    assert data["deleted_chunks"] == 3
    assert fake_store.removed_document_id == "doc-reindex"
    assert fake_store.added_kwargs["content_hash"] == content_hash


def test_parse_pdf_index_file_passes_ocr_options(monkeypatch):
    calls = {}

    def fake_extract_text_from_pdf_bytes(
        filename,
        content,
        enable_ocr=False,
        ocr_language="chi_sim+eng",
        extract_tables=False,
        enable_image_ocr=False,
    ):
        calls["filename"] = filename
        calls["enable_ocr"] = enable_ocr
        calls["ocr_language"] = ocr_language
        calls["extract_tables"] = extract_tables
        calls["enable_image_ocr"] = enable_image_ocr
        return ExtractedPdf(
            filename=filename,
            page_count=1,
            char_count=13,
            preview="ocr text",
            pages=[
                ExtractedPage(
                    page_number=1,
                    char_count=13,
                    preview="ocr text",
                    text="ocr text here",
                    extraction_method="pdf_ocr",
                )
            ],
            scanned_like=False,
            extraction_mode="ocr",
            ocr_page_count=1,
        )

    monkeypatch.setattr(main, "extract_text_from_pdf_bytes", fake_extract_text_from_pdf_bytes)
    monkeypatch.setattr(
        main,
        "split_pdf_text",
        lambda extracted, chunk_size, overlap: [
            TextChunk(chunk_id=1, page_number=1, char_count=13, text="ocr text here", extraction_method="pdf_ocr")
        ],
    )

    file_type, page_count, chunks, extraction_mode, ocr_page_count, image_ocr_count, extraction_methods = main._parse_and_split_index_file(
        filename="scan.pdf",
        content=b"%PDF",
        chunk_size=800,
        overlap=100,
        enable_ocr=True,
        ocr_language="eng",
    )

    assert file_type == "pdf"
    assert page_count == 1
    assert chunks[0].extraction_method == "pdf_ocr"
    assert extraction_mode == "ocr"
    assert ocr_page_count == 1
    assert image_ocr_count == 0
    assert extraction_methods == ["pdf_ocr"]
    assert calls["enable_ocr"] is True
    assert calls["ocr_language"] == "eng"
    assert calls["extract_tables"] is False
    assert calls["enable_image_ocr"] is False


def test_parse_pdf_index_file_passes_table_option(monkeypatch):
    calls = {}

    def fake_extract_text_from_pdf_bytes(
        filename,
        content,
        enable_ocr=False,
        ocr_language="chi_sim+eng",
        extract_tables=False,
        enable_image_ocr=False,
    ):
        calls["extract_tables"] = extract_tables
        calls["enable_image_ocr"] = enable_image_ocr
        return ExtractedPdf(
            filename=filename,
            page_count=1,
            char_count=78,
            preview="Project pricing",
            pages=[
                ExtractedPage(
                    page_number=1,
                    char_count=15,
                    preview="Project pricing",
                    text="Project pricing",
                    tables=[
                        ExtractedTable(
                            table_number=1,
                            row_count=2,
                            char_count=63,
                            preview="pdf table 1 page 1 row 2: Project=Falcon",
                            text="pdf table 1 page 1 row 2: Project=Falcon; Price=999",
                        )
                    ],
                )
            ],
            scanned_like=False,
            extraction_mode="text_table",
            table_count=1,
        )

    monkeypatch.setattr(main, "extract_text_from_pdf_bytes", fake_extract_text_from_pdf_bytes)

    file_type, page_count, chunks, extraction_mode, ocr_page_count, image_ocr_count, extraction_methods = main._parse_and_split_index_file(
        filename="pricing.pdf",
        content=b"%PDF",
        chunk_size=100,
        overlap=0,
        extract_tables=True,
    )

    assert file_type == "pdf"
    assert page_count == 1
    assert calls["extract_tables"] is True
    assert calls["enable_image_ocr"] is False
    assert extraction_mode == "text_table"
    assert ocr_page_count == 0
    assert image_ocr_count == 0
    assert [chunk.extraction_method for chunk in chunks] == ["text", "pdf_table"]
    assert extraction_methods == ["pdf_table", "text"]


def test_parse_pdf_index_file_passes_image_ocr_option(monkeypatch):
    calls = {}

    def fake_extract_text_from_pdf_bytes(
        filename,
        content,
        enable_ocr=False,
        ocr_language="chi_sim+eng",
        extract_tables=False,
        enable_image_ocr=False,
    ):
        calls["enable_image_ocr"] = enable_image_ocr
        calls["ocr_language"] = ocr_language
        return ExtractedPdf(
            filename=filename,
            page_count=1,
            char_count=48,
            preview="Architecture overview",
            pages=[
                ExtractedPage(
                    page_number=1,
                    char_count=21,
                    preview="Architecture overview",
                    text="Architecture overview",
                    images=[
                        ExtractedImage(
                            image_number=1,
                            char_count=27,
                            preview="Gateway to Qdrant",
                            text="Gateway to Qdrant diagram",
                        )
                    ],
                )
            ],
            scanned_like=False,
            extraction_mode="text_image_ocr",
            image_ocr_count=1,
        )

    monkeypatch.setattr(main, "extract_text_from_pdf_bytes", fake_extract_text_from_pdf_bytes)

    file_type, page_count, chunks, extraction_mode, ocr_page_count, image_ocr_count, extraction_methods = main._parse_and_split_index_file(
        filename="diagram.pdf",
        content=b"%PDF",
        chunk_size=100,
        overlap=0,
        enable_image_ocr=True,
        ocr_language="eng",
    )

    assert file_type == "pdf"
    assert page_count == 1
    assert calls["enable_image_ocr"] is True
    assert calls["ocr_language"] == "eng"
    assert extraction_mode == "text_image_ocr"
    assert ocr_page_count == 0
    assert image_ocr_count == 1
    assert [chunk.extraction_method for chunk in chunks] == ["text", "pdf_image_ocr"]
    assert extraction_methods == ["pdf_image_ocr", "text"]


def test_parse_non_pdf_index_file_counts_image_ocr_chunks(monkeypatch):
    def fake_load_document_from_bytes(filename, content, enable_image_ocr=False, ocr_language="chi_sim+eng"):
        assert enable_image_ocr is True
        assert ocr_language == "eng"
        return ParsedDocument(
            filename=filename,
            file_type="docx",
            char_count=20,
            preview="ImageProject OCR",
            sections=[
                ParsedSection(
                    section_number=1,
                    title="docx image 1 OCR",
                    text="ImageProject OCR text",
                    extraction_method="image_ocr",
                )
            ],
        )

    monkeypatch.setattr(main, "load_document_from_bytes", fake_load_document_from_bytes)

    file_type, page_count, chunks, extraction_mode, ocr_page_count, image_ocr_count, extraction_methods = main._parse_and_split_index_file(
        filename="demo.docx",
        content=b"docx bytes",
        chunk_size=100,
        overlap=0,
        enable_image_ocr=True,
        ocr_language="eng",
    )

    assert file_type == "docx"
    assert page_count == 1
    assert chunks[0].extraction_method == "image_ocr"
    assert extraction_mode is None
    assert ocr_page_count == 0
    assert image_ocr_count == 1
    assert extraction_methods == ["image_ocr"]


def test_index_document_accepts_txt_file(tmp_path, monkeypatch):
    class FakeDocumentStore:
        def __init__(self):
            self.added_kwargs = None

        def get_document_by_content_hash(self, value, **kwargs):
            return None

        def add_document(self, **kwargs):
            self.added_kwargs = kwargs
            return DocumentRecord(
                document_id=kwargs["document_id"],
                filename=kwargs["filename"],
                file_type=kwargs["file_type"],
                content_hash=kwargs["content_hash"],
                content_hash_prefix=kwargs["content_hash"][:12],
                chunk_count=kwargs["chunk_count"],
                created_at="2026-06-03T00:00:00+00:00",
                indexed_at="2026-06-03T00:00:00+00:00",
                source_file_size=kwargs["source_file_size"],
                collection=kwargs["collection"],
                chunk_size=kwargs["chunk_size"],
                overlap=kwargs["overlap"],
                embedding_model=kwargs["embedding_model"],
                page_count=kwargs["page_count"],
                indexed_count=kwargs["indexed_count"],
            )

    fake_store = FakeDocumentStore()
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(
            deepseek_api_key="",
            document_metadata_path="unused.json",
            source_storage_enabled=True,
            source_storage_backend="local",
            source_storage_path=str(tmp_path / "source_files"),
        ),
    )
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: fake_store)
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda *args, **kwargs: object())
    monkeypatch.setattr(main, "ensure_collection", lambda client, collection_name, dimension: None)
    monkeypatch.setattr(main, "upsert_chunks", lambda **kwargs: len(kwargs["chunks"]))

    client = TestClient(main.app)
    response = client.post(
        "/documents/index",
        files={"file": ("notes.txt", "RAG 本地知识库可以索引纯文本资料。".encode("utf-8"), "text/plain")},
        data={"chunk_size": "100", "overlap": "0"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "text"
    assert data["indexed"] is True
    assert data["source_storage_backend"] == "local"
    assert data["source_storage_key"].endswith("-notes.txt")
    assert fake_store.added_kwargs["file_type"] == "text"
    assert fake_store.added_kwargs["source_storage_backend"] == "local"
    assert (tmp_path / "source_files" / data["source_storage_key"]).exists()


def test_index_document_accepts_html_file(monkeypatch):
    class FakeDocumentStore:
        def __init__(self):
            self.added_kwargs = None

        def get_document_by_content_hash(self, value, **kwargs):
            return None

        def add_document(self, **kwargs):
            self.added_kwargs = kwargs
            return DocumentRecord(
                document_id=kwargs["document_id"],
                filename=kwargs["filename"],
                file_type=kwargs["file_type"],
                content_hash=kwargs["content_hash"],
                content_hash_prefix=kwargs["content_hash"][:12],
                chunk_count=kwargs["chunk_count"],
                created_at="2026-06-03T00:00:00+00:00",
                indexed_at="2026-06-03T00:00:00+00:00",
                source_file_size=kwargs["source_file_size"],
                collection=kwargs["collection"],
                chunk_size=kwargs["chunk_size"],
                overlap=kwargs["overlap"],
                embedding_model=kwargs["embedding_model"],
                page_count=kwargs["page_count"],
                indexed_count=kwargs["indexed_count"],
            )

    fake_store = FakeDocumentStore()
    captured = {}
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="", document_metadata_path="unused.json"),
    )
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: fake_store)
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda *args, **kwargs: object())
    monkeypatch.setattr(main, "ensure_collection", lambda client, collection_name, dimension: None)

    def fake_upsert_chunks(**kwargs):
        captured["chunks"] = kwargs["chunks"]
        captured["file_type"] = kwargs["file_type"]
        return len(kwargs["chunks"])

    monkeypatch.setattr(main, "upsert_chunks", fake_upsert_chunks)

    html = """
    <html><head><title>Wiki Page</title><script>ignore()</script></head>
    <body><main><h1>Falcon HTML</h1><p>HTML pages can enter RAG.</p></main></body></html>
    """

    client = TestClient(main.app)
    response = client.post(
        "/documents/index",
        files={"file": ("wiki.html", html.encode("utf-8"), "text/html")},
        data={"chunk_size": "100", "overlap": "0"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "html"
    assert data["indexed"] is True
    assert fake_store.added_kwargs["file_type"] == "html"
    assert captured["file_type"] == "html"
    assert captured["chunks"][0].extraction_method == "text"
    assert "Falcon HTML" in captured["chunks"][0].text
    assert "ignore" not in captured["chunks"][0].text


def test_index_web_page_fetches_and_indexes_html(tmp_path, monkeypatch):
    class FakeDocumentStore:
        def __init__(self):
            self.added_kwargs = None

        def get_document_by_content_hash(self, value, **kwargs):
            return None

        def add_document(self, **kwargs):
            self.added_kwargs = kwargs
            return DocumentRecord(
                document_id=kwargs["document_id"],
                filename=kwargs["filename"],
                file_type=kwargs["file_type"],
                content_hash=kwargs["content_hash"],
                content_hash_prefix=kwargs["content_hash"][:12],
                chunk_count=kwargs["chunk_count"],
                created_at="2026-06-03T00:00:00+00:00",
                indexed_at="2026-06-03T00:00:00+00:00",
                source_file_size=kwargs["source_file_size"],
                collection=kwargs["collection"],
                chunk_size=kwargs["chunk_size"],
                overlap=kwargs["overlap"],
                embedding_model=kwargs["embedding_model"],
                page_count=kwargs["page_count"],
                indexed_count=kwargs["indexed_count"],
            )

    settings = Settings(
        deepseek_api_key="",
        document_metadata_path="unused.json",
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        web_fetch_enabled=True,
    )
    fake_store = FakeDocumentStore()
    captured = {}
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: fake_store)
    monkeypatch.setattr(
        main,
        "fetch_web_page",
        lambda **kwargs: FetchedWebPage(
            url=kwargs["url"],
            final_url="https://example.com/docs/intro",
            filename="example.com-docs-intro.html",
            content=b"<html><head><title>Docs</title></head><body><main><h1>Web Falcon</h1></main></body></html>",
            content_type="text/html",
            status_code=200,
        ),
    )
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda *args, **kwargs: object())
    monkeypatch.setattr(main, "ensure_collection", lambda client, collection_name, dimension: None)

    def fake_upsert_chunks(**kwargs):
        captured["chunks"] = kwargs["chunks"]
        captured["file_type"] = kwargs["file_type"]
        return len(kwargs["chunks"])

    monkeypatch.setattr(main, "upsert_chunks", fake_upsert_chunks)

    client = TestClient(main.app)
    response = client.post(
        "/web-pages/index",
        json={"url": "https://example.com/docs/intro", "chunk_size": 100, "overlap": 0},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "html"
    assert data["filename"] == "example.com-docs-intro.html"
    assert fake_store.added_kwargs["file_type"] == "html"
    assert captured["file_type"] == "html"
    assert "Web Falcon" in captured["chunks"][0].text

    with session_scope(settings.database_url) as session:
        audit = session.scalar(select(AuditLogModel).where(AuditLogModel.action == "web_page.index"))
        assert audit is not None
        assert audit.status == "success"


def test_index_web_page_records_fetch_failure_audit(tmp_path, monkeypatch):
    settings = Settings(
        deepseek_api_key="",
        database_url=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
        web_fetch_enabled=True,
    )
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(
        main,
        "fetch_web_page",
        lambda **kwargs: (_ for _ in ()).throw(WebPageFetchError("Private or local URLs are not allowed")),
    )

    client = TestClient(main.app)
    response = client.post("/web-pages/index", json={"url": "http://127.0.0.1/admin"})

    assert response.status_code == 422
    assert "Private or local URLs" in response.json()["detail"]

    with session_scope(settings.database_url) as session:
        audit = session.scalar(select(AuditLogModel).where(AuditLogModel.action == "web_page.index"))
        assert audit is not None
        assert audit.status == "failure"


def test_index_document_accepts_csv_file(monkeypatch):
    class FakeDocumentStore:
        def __init__(self):
            self.added_kwargs = None

        def get_document_by_content_hash(self, value, **kwargs):
            return None

        def add_document(self, **kwargs):
            self.added_kwargs = kwargs
            return DocumentRecord(
                document_id=kwargs["document_id"],
                filename=kwargs["filename"],
                file_type=kwargs["file_type"],
                content_hash=kwargs["content_hash"],
                content_hash_prefix=kwargs["content_hash"][:12],
                chunk_count=kwargs["chunk_count"],
                created_at="2026-06-03T00:00:00+00:00",
                indexed_at="2026-06-03T00:00:00+00:00",
                source_file_size=kwargs["source_file_size"],
                collection=kwargs["collection"],
                chunk_size=kwargs["chunk_size"],
                overlap=kwargs["overlap"],
                embedding_model=kwargs["embedding_model"],
                page_count=kwargs["page_count"],
                indexed_count=kwargs["indexed_count"],
            )

    fake_store = FakeDocumentStore()
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="", document_metadata_path="unused.json"),
    )
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: fake_store)
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda *args, **kwargs: object())
    monkeypatch.setattr(main, "ensure_collection", lambda client, collection_name, dimension: None)
    monkeypatch.setattr(main, "upsert_chunks", lambda **kwargs: len(kwargs["chunks"]))

    client = TestClient(main.app)
    response = client.post(
        "/documents/index",
        files={"file": ("projects.csv", "name,owner\nCsvRocket,Dana\n".encode("utf-8"), "text/csv")},
        data={"chunk_size": "100", "overlap": "0"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["file_type"] == "csv"
    assert data["indexed"] is True
    assert fake_store.added_kwargs["file_type"] == "csv"
