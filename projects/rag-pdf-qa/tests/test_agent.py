from fastapi.testclient import TestClient

import app.main as main
from app.agent import decide_agent_route
from app.config import Settings
from app.vector_store import SearchResult


def test_decide_agent_route_prefers_chat_for_small_talk():
    assert decide_agent_route("你好") == "chat"
    assert decide_agent_route("谢谢你") == "chat"


def test_decide_agent_route_prefers_rag_for_document_questions():
    assert decide_agent_route("GUI Agent 的核心流程是什么？") == "rag"
    assert decide_agent_route("请根据知识库回答这个 PDF 的结论") == "rag"


def test_agent_ask_appears_in_openapi():
    client = TestClient(main.app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/agent/ask" in response.json()["paths"]


def test_agent_ask_routes_small_talk_to_chat(monkeypatch):
    class FakeDeepSeekClient:
        def __init__(self, settings):
            self.settings = settings

        async def chat(self, message):
            assert message == "你好"
            return {
                "reply": "你好，我是本地 RAG 助手。",
                "model": "fake-chat-model",
                "usage": {"total_tokens": 8},
            }

        async def chat_messages(self, *args, **kwargs):
            raise AssertionError("chat route should not call RAG answer generation")

    def fail_embed(*args, **kwargs):
        raise AssertionError("chat route should not search local chunks")

    monkeypatch.setattr(main, "get_settings", lambda: Settings(deepseek_api_key="test"))
    monkeypatch.setattr(main, "DeepSeekClient", FakeDeepSeekClient)
    monkeypatch.setattr(main, "embed_text", fail_embed)

    client = TestClient(main.app)
    response = client.post("/agent/ask", json={"question": "你好"})

    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "chat"
    assert data["route_reason"]
    assert data["tools_used"] == ["llm_chat"]
    assert data["routing_debug"]["selected_route"] == "chat"
    assert data["routing_debug"]["fallback"] is None
    assert data["reply"] == "你好，我是本地 RAG 助手。"
    assert data["source_count"] == 0
    assert data["sources"] == []
    assert data["usage"]["total_tokens"] == 8


def test_agent_ask_routes_document_question_to_rag(monkeypatch):
    class FakeDeepSeekClient:
        def __init__(self, settings):
            self.settings = settings

        async def chat(self, message):
            raise AssertionError("RAG route should not call direct chat")

        async def chat_messages(self, messages, max_tokens, temperature):
            prompt_text = "\n".join(message["content"] for message in messages)
            assert "[Source 1]" in prompt_text
            return {
                "reply": "答案：\n- GUI Agent 会观察、规划、执行。\n\n依据：\n- [Source 1] 支持该流程。\n\n资料不足之处：\n- 未发现明显不足。",
                "model": "fake-rag-model",
                "usage": {"total_tokens": 42},
            }

    def fake_search_chunks(client, collection_name, query_vector, limit, document_id=None, file_type=None):
        assert limit == 3
        assert document_id is None
        assert file_type is None
        return [
            SearchResult(
                point_id="point-1",
                score=0.82,
                document_id="doc-1",
                file_type="pdf",
                filename="demo.pdf",
                page_number=2,
                chunk_id=4,
                text="GUI Agent follows observe, plan, and act steps.",
            )
        ]

    monkeypatch.setattr(main, "get_settings", lambda: Settings(deepseek_api_key="test"))
    monkeypatch.setattr(main, "DeepSeekClient", FakeDeepSeekClient)
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())
    monkeypatch.setattr(main, "search_chunks", fake_search_chunks)

    client = TestClient(main.app)
    response = client.post(
        "/agent/ask",
        json={"question": "GUI Agent 的核心流程是什么？", "limit": 3, "score_threshold": 0.5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "rag"
    assert "知识库" in data["route_reason"] or "资料" in data["route_reason"]
    assert data["tools_used"] == ["local_embedding", "qdrant_search", "llm_rag"]
    assert data["routing_debug"]["selected_route"] == "rag"
    assert data["routing_debug"]["retrieved_count"] == 1
    assert data["routing_debug"]["filtered_count"] == 1
    assert data["routing_debug"]["fallback"] is None
    assert data["model"] == "fake-rag-model"
    assert data["retrieved_count"] == 1
    assert data["source_count"] == 1
    assert data["sources"][0]["source_id"] == 1
    assert data["sources"][0]["filename"] == "demo.pdf"


def test_agent_ask_returns_insufficient_context_without_calling_deepseek(monkeypatch):
    class FakeDeepSeekClient:
        def __init__(self, settings):
            self.settings = settings

        async def chat(self, *args, **kwargs):
            raise AssertionError("insufficient_context route should not call DeepSeek")

        async def chat_messages(self, *args, **kwargs):
            raise AssertionError("insufficient_context route should not call DeepSeek")

    monkeypatch.setattr(main, "get_settings", lambda: Settings(deepseek_api_key="test"))
    monkeypatch.setattr(main, "DeepSeekClient", FakeDeepSeekClient)
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())
    monkeypatch.setattr(main, "search_chunks", lambda client, collection_name, query_vector, limit, document_id=None, file_type=None: [])

    client = TestClient(main.app)
    response = client.post(
        "/agent/ask",
        json={"question": "请根据知识库回答 FireDragon-404 是什么？", "limit": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "insufficient_context"
    assert "没有返回任何相关 chunk" in data["route_reason"]
    assert data["tools_used"] == ["local_embedding", "qdrant_search"]
    assert data["routing_debug"]["fallback"] == "no_retrieved_chunks"
    assert "资料不足" in data["reply"]
    assert data["retrieved_count"] == 0
    assert data["source_count"] == 0
    assert data["sources"] == []


def test_agent_ask_returns_threshold_fallback_reason(monkeypatch):
    class FakeDeepSeekClient:
        def __init__(self, settings):
            self.settings = settings

        async def chat(self, *args, **kwargs):
            raise AssertionError("threshold fallback should not call DeepSeek")

        async def chat_messages(self, *args, **kwargs):
            raise AssertionError("threshold fallback should not call DeepSeek")

    monkeypatch.setattr(main, "get_settings", lambda: Settings(deepseek_api_key="test"))
    monkeypatch.setattr(main, "DeepSeekClient", FakeDeepSeekClient)
    monkeypatch.setattr(main, "embed_text", lambda text, model_name: [0.1, 0.2, 0.3])
    monkeypatch.setattr(main, "get_qdrant_client", lambda local_path: object())
    monkeypatch.setattr(
        main,
        "search_chunks",
        lambda client, collection_name, query_vector, limit, document_id=None, file_type=None: [
            SearchResult(
                point_id="point-low",
                score=0.2,
                document_id="doc-1",
                file_type="pdf",
                filename="demo.pdf",
                page_number=1,
                chunk_id=1,
                text="低分检索结果。",
            )
        ],
    )

    client = TestClient(main.app)
    response = client.post(
        "/agent/ask",
        json={"question": "请根据知识库回答 GUI Agent 是什么？", "limit": 5, "score_threshold": 0.9},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "insufficient_context"
    assert "score_threshold" in data["route_reason"]
    assert data["tools_used"] == ["local_embedding", "qdrant_search"]
    assert data["routing_debug"]["retrieved_count"] == 1
    assert data["routing_debug"]["filtered_count"] == 0
    assert data["routing_debug"]["fallback"] == "score_threshold_filtered_all"
