import json
from dataclasses import dataclass, field
from typing import Any, Protocol


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def coerce_arguments(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return parsed
    return {}


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class ProviderResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    model: str
    tool_calls: list[ToolCall] = field(default_factory=list)


class ModelProvider(Protocol):
    name: str
    model: str

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
        json_schema: dict[str, Any] | None = None,
    ) -> ProviderResult: ...

    async def aclose(self) -> None: ...
