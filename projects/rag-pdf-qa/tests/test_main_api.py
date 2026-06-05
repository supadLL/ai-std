from fastapi.testclient import TestClient

import app.main as main
from app.config import Settings
from app.document_loaders import ParsedDocument, ParsedSection
from app.document_store import DocumentRecord
from app.pdf_extractor import ExtractedPage, ExtractedPdf
from app.runtime_settings import RuntimeSettings
from app.text_splitter import TextChunk
from app.vector_store import SearchResult


def test_search_documents_returns_retrieved_results(monkeypatch):
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())

    def fake_search_chunks(client, collection_name, query_vector, limit, document_id=None, file_type=None):
        assert limit == 2
        assert document_id == "doc-1"
        assert file_type == "pdf"
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
    assert "/web/styles.css?v=40" in app_response.text
    assert "/web/app.js?v=40" in app_response.text
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
    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    assert openapi_response.json()["info"]["title"] == "Local Knowledge RAG Agent"
    assert "/documents/index" in openapi_response.json()["paths"]
    assert "/evaluation/questions" in openapi_response.json()["paths"]
    assert "/evaluation/latest" in openapi_response.json()["paths"]
    assert "/evaluation/run" in openapi_response.json()["paths"]


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

    def fake_run_rag_search_evaluation(*, settings, limit, score_threshold):
        assert settings.qdrant_collection
        assert limit == 3
        assert score_threshold is None
        return fake_result

    monkeypatch.setattr(main, "run_rag_search_evaluation", fake_run_rag_search_evaluation)
    monkeypatch.setattr(main, "read_latest_evaluation", lambda: fake_result)

    client = TestClient(main.app)

    questions_response = client.get("/evaluation/questions")
    run_response = client.post("/evaluation/run", json={"limit": 3})
    latest_response = client.get("/evaluation/latest")

    assert questions_response.status_code == 200
    assert questions_response.json()["case_count"] == 1
    assert questions_response.json()["questions"][0]["expected_keywords"] == ["检索"]
    assert run_response.status_code == 200
    assert run_response.json()["hit_rate"] == 1.0
    assert run_response.json()["cases"][0]["top_sources"][0]["filename"] == "demo.md"
    assert latest_response.status_code == 200
    assert latest_response.json()["dataset_name"] == "demo_eval"


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

        def list_documents(self):
            return list(self.records.values())

        def get_document(self, document_id):
            return self.records.get(document_id)

        def remove_document(self, document_id):
            return self.records.pop(document_id, None)

    fake_store = FakeDocumentStore()
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="", document_metadata_path="unused.json"),
    )
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: fake_store)
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())
    monkeypatch.setattr(main, "delete_document_chunks", lambda client, collection_name, document_id: 3)

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
        def get_document(self, document_id):
            return records.get(document_id)

        def remove_document(self, document_id):
            return records.pop(document_id, None)

    deleted_ids = []
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: Settings(deepseek_api_key="", document_metadata_path="unused.json"),
    )
    monkeypatch.setattr(main, "get_document_store", lambda metadata_path: FakeDocumentStore())
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())

    def fake_delete_document_chunks(client, collection_name, document_id):
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

        def get_document(self, document_id):
            return self.record if document_id == "doc-1" else None

        def remove_document(self, document_id):
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
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())
    monkeypatch.setattr(main, "ensure_collection", lambda client, collection_name, dimension: None)
    monkeypatch.setattr(main, "delete_document_chunks", lambda client, collection_name, document_id: 1)
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
        def get_document_by_content_hash(self, value):
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

        def get_document_by_content_hash(self, value):
            assert value == content_hash
            return record

        def remove_document(self, document_id):
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
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())
    monkeypatch.setattr(main, "ensure_collection", lambda client, collection_name, dimension: None)
    monkeypatch.setattr(main, "delete_document_chunks", lambda client, collection_name, document_id: 3)
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

    def fake_extract_text_from_pdf_bytes(filename, content, enable_ocr=False, ocr_language="chi_sim+eng"):
        calls["filename"] = filename
        calls["enable_ocr"] = enable_ocr
        calls["ocr_language"] = ocr_language
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


def test_index_document_accepts_txt_file(monkeypatch):
    class FakeDocumentStore:
        def __init__(self):
            self.added_kwargs = None

        def get_document_by_content_hash(self, value):
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
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())
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
    assert fake_store.added_kwargs["file_type"] == "text"


def test_index_document_accepts_csv_file(monkeypatch):
    class FakeDocumentStore:
        def __init__(self):
            self.added_kwargs = None

        def get_document_by_content_hash(self, value):
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
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())
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
