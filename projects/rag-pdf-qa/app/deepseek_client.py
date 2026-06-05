from typing import Any

import httpx

from app.config import Settings
from app.llm_providers import get_provider_option


class DeepSeekClientError(RuntimeError):
    pass


class DeepSeekClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def chat(self, message: str) -> dict[str, Any]:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a concise and reliable AI learning assistant. "
                    "Answer concretely and prefer Chinese."
                ),
            },
            {"role": "user", "content": message},
        ]
        return await self.chat_messages(messages=messages, max_tokens=1000, temperature=0.2)

    async def chat_messages(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        provider_option = get_provider_option(self._settings.llm_provider)
        if provider_option.api_key_required and not self._settings.llm_api_key:
            raise DeepSeekClientError("LLM_API_KEY is not configured")

        url = f"{self._settings.llm_base_url}/chat/completions"
        payload = {
            "model": self._settings.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Content-Type": "application/json",
        }
        if self._settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self._settings.llm_api_key}"

        try:
            async with httpx.AsyncClient(timeout=self._settings.request_timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise DeepSeekClientError(f"{provider_option.label} request timed out") from exc
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            raise DeepSeekClientError(
                f"{provider_option.label} returned HTTP {exc.response.status_code}: {body}"
            ) from exc
        except httpx.HTTPError as exc:
            raise DeepSeekClientError(f"{provider_option.label} request failed: {exc}") from exc

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise DeepSeekClientError("LLM response has no choices")

        content = choices[0].get("message", {}).get("content")
        if not content:
            raise DeepSeekClientError("LLM response content is empty")

        return {
            "reply": content,
            "model": data.get("model", self._settings.llm_model),
            "usage": data.get("usage"),
        }
