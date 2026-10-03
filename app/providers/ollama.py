import json
from typing import Any

import httpx

from app.config import Settings
from app.providers.base import ProviderResult, ToolCall, coerce_arguments, estimate_tokens
from app.providers.errors import ProviderError


class OllamaProvider:
    """Local open-model backend. Requires a running Ollama server."""

    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.model = settings.ollama_model
        self._client = httpx.AsyncClient(
            base_url=settings.ollama_base_url.rstrip("/"),
            timeout=settings.request_timeout_seconds,
        )

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
        json_schema: dict[str, Any] | None = None,
    ) -> ProviderResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if tools:
            payload["tools"] = tools
        if json_schema is not None:
            payload["format"] = "json"
        try:
            response = await self._client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            raise ProviderError("Ollama request failed") from exc
        return _parse_ollama(data, messages, self.model)

    async def aclose(self) -> None:
        await self._client.aclose()


def _parse_ollama(
    data: dict[str, Any], messages: list[dict[str, str]], model: str
) -> ProviderResult:
    message = data.get("message") or {}
    content = message.get("content") or ""
    tool_calls: list[ToolCall] = []
    for call in message.get("tool_calls") or []:
        function = call.get("function") or call
        name = function.get("name")
        if not isinstance(name, str):
            continue
        tool_calls.append(
            ToolCall(name=name, arguments=coerce_arguments(function.get("arguments")))
        )
    prompt_tokens = int(data.get("prompt_eval_count") or 0)
    completion_tokens = int(data.get("eval_count") or 0)
    if prompt_tokens == 0:
        prompt_tokens = sum(estimate_tokens(item.get("content", "")) for item in messages)
    if completion_tokens == 0:
        completion_tokens = estimate_tokens(content) or (1 if tool_calls else 0)
    return ProviderResult(
        content=content,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model=str(data.get("model") or model),
        tool_calls=tool_calls,
    )
