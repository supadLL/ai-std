import pytest

from app.config import Settings
from app.deepseek_client import DeepSeekClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_llm_client_uses_generic_openai_compatible_settings(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "model": "provider-returned-model",
                "choices": [{"message": {"content": "hello"}}],
                "usage": {"total_tokens": 3},
            }

    class FakeAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr("app.deepseek_client.httpx.AsyncClient", FakeAsyncClient)

    client = DeepSeekClient(
        Settings(
            llm_provider="qwen",
            llm_api_key="test-key",
            llm_base_url="https://runtime.example/v1",
            llm_model="runtime-model",
            request_timeout_seconds=12,
        )
    )

    result = await client.chat_messages(messages=[{"role": "user", "content": "hi"}])

    assert captured["url"] == "https://runtime.example/v1/chat/completions"
    assert captured["json"]["model"] == "runtime-model"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    assert captured["timeout"] == 12
    assert result["reply"] == "hello"
    assert result["model"] == "provider-returned-model"


@pytest.mark.anyio
async def test_ollama_provider_does_not_require_api_key(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "local"}}]}

    class FakeAsyncClient:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, json, headers):
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr("app.deepseek_client.httpx.AsyncClient", FakeAsyncClient)

    client = DeepSeekClient(
        Settings(
            llm_provider="ollama",
            llm_api_key="",
            llm_base_url="http://127.0.0.1:11434/v1",
            llm_model="qwen2.5",
        )
    )

    result = await client.chat_messages(messages=[{"role": "user", "content": "hi"}])

    assert "Authorization" not in captured["headers"]
    assert result["reply"] == "local"
