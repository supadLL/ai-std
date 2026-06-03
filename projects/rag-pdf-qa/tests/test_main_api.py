from fastapi.testclient import TestClient

import app.main as main
from app.config import Settings
from app.document_store import DocumentRecord
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


def test_build_rag_messages_requires_stable_output_format():
    messages = main._build_rag_messages(
        question="GUI Agent 的核心流程是什么？",
        results=[
            SearchResult(
                point_id="point-1",
                score=0.82,
                document_id="doc-1",
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
    assert "[Source 1]" in prompt_text


def test_document_management_endpoints(monkeypatch):
    record = DocumentRecord(
        document_id="doc-1",
        filename="demo.pdf",
        file_type="pdf",
        chunk_count=3,
        created_at="2026-06-03T00:00:00+00:00",
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
