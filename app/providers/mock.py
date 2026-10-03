import json
from typing import Any

from app.providers.base import ProviderResult, ToolCall, estimate_tokens


def _latest_user(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def _prompt_tokens(messages: list[dict[str, str]]) -> int:
    return sum(estimate_tokens(message.get("content", "")) for message in messages)


class MockProvider:
    """Deterministic backend used for tests and laptops without a model server."""

    name = "mock"
    model = "mock-model"

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
        json_schema: dict[str, Any] | None = None,
    ) -> ProviderResult:
        del temperature, max_tokens, json_schema
        latest = _latest_user(messages)
        joined = "\n".join(message.get("content", "") for message in messages)
        content = self._content(latest, joined, tools)
        tool_calls = self._tool_calls(latest, tools)
        if tool_calls:
            content = ""
        return ProviderResult(
            content=content,
            prompt_tokens=_prompt_tokens(messages),
            completion_tokens=estimate_tokens(content) or 1,
            model=self.model,
            tool_calls=tool_calls,
        )

    async def aclose(self) -> None:
        return None

    def _content(self, latest: str, joined: str, tools: list[dict[str, Any]] | None) -> str:
        if latest.startswith("Tool result for "):
            return f"Tool finished. {latest}"
        if "SCHEMA_NAME=task" in joined:
            return _task_json(latest)
        if "SCHEMA_NAME=sentiment" in joined:
            return _sentiment_json(latest)
        if tools and _wants_tool(latest):
            return ""
        clipped = latest[:200]
        return f"Mock reply: {clipped}"

    def _tool_calls(self, latest: str, tools: list[dict[str, Any]] | None) -> list[ToolCall]:
        if not tools or latest.startswith("Tool result for "):
            return []
        lowered = latest.lower()
        if "model card" in lowered or "context window" in lowered:
            return [ToolCall(name="model_card", arguments={"model_name": "llama3.2"})]
        if "token" in lowered:
            return [ToolCall(name="estimate_tokens", arguments={"text": latest})]
        return []


def _wants_tool(latest: str) -> bool:
    lowered = latest.lower()
    return "token" in lowered or "model card" in lowered or "context window" in lowered


def _task_json(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("urgent", "asap", "immediately")):
        priority = "high"
    elif any(word in lowered for word in ("later", "someday")):
        priority = "low"
    else:
        priority = "medium"
    title = " ".join(text.split())[:100] or "Untitled task"
    return json.dumps({"title": title, "priority": priority, "tags": ["extracted"]})


def _sentiment_json(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("love", "great", "excellent", "good")):
        label = "positive"
        rationale = "The text uses positive language."
    elif any(word in lowered for word in ("hate", "terrible", "bad", "awful")):
        label = "negative"
        rationale = "The text uses negative language."
    else:
        label = "neutral"
        rationale = "The text does not lean positive or negative."
    return json.dumps({"label": label, "confidence": 0.9, "rationale": rationale})
