from fastapi.testclient import TestClient

import app.main as main
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
    assert data["results"][0]["chunk_id"] == 7


def test_build_rag_messages_requires_stable_output_format():
    messages = main._build_rag_messages(
        question="GUI Agent 的核心流程是什么？",
        results=[
            SearchResult(
                point_id="point-1",
                score=0.82,
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

