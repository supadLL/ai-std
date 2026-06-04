from fastapi.testclient import TestClient

import app.main as main
from app.config import Settings
from app.document_store import DocumentRecord
from app.pdf_extractor import ExtractedPage, ExtractedPdf
from app.runtime_settings import RuntimeSettings
from app.text_splitter import TextChunk
from app.vector_store import SearchResult


def test_search_documents_returns_retrieved_results(monkeypatch):
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())

    def fake_search_chunks(client, collection_name, query_vector, limit):
        assert limit == 2
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
    response = client.post("/documents/search", json={"query": "GUI Agent flow", "limit": 2})

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "GUI Agent flow"
    assert data["limit"] == 2
    assert data["results"][0]["filename"] == "demo.pdf"
    assert data["results"][0]["document_id"] == "doc-1"
    assert data["results"][0]["chunk_id"] == 7


def test_web_ui_routes_are_available():
    client = TestClient(main.app)

    app_response = client.get("/app")
    docs_response = client.get("/docs")
    openapi_response = client.get("/openapi.json")

    assert app_response.status_code == 200
    assert "Local Knowledge RAG Agent" in app_response.text
    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    assert openapi_response.json()["info"]["title"] == "Local Knowledge RAG Agent"
    assert "/documents/index" in openapi_response.json()["paths"]


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
    assert data["api_key_configured"] is True
    assert data["api_key_source"] == "env"
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
            "deepseek_api_key": "runtime-secret",
            "deepseek_base_url": "https://runtime.example",
            "deepseek_model": "runtime-model",
            "request_timeout_seconds": 60,
            "rag_system_prompt": "runtime system",
            "rag_answer_instructions": "runtime answer",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["api_key_configured"] is True
    assert data["api_key_source"] == "runtime"
    assert data["deepseek_model"] == "runtime-model"
    assert "runtime-secret" not in response.text
    assert saved["runtime_settings"].deepseek_api_key == "runtime-secret"
    assert saved["runtime_settings"].rag_answer_instructions == "runtime answer"


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
        lambda filename, content: ExtractedPdf(
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
