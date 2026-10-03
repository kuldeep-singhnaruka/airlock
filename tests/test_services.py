import asyncio

import pytest

from app.config import DEV_JWT_SECRET, Settings, ensure_production_secret
from app.providers.base import ProviderResult
from app.providers.factory import build_provider
from app.providers.ollama import _parse_ollama
from app.providers.openai_compatible import _parse_openai
from app.schemas.inference import StructuredRequest
from app.services.errors import SchemaMismatchError
from app.services.inference import InferenceService
from app.services.rate_limit import RateLimitExceeded, SlidingWindowLimiter
from app.services.usage import UsageLedger


class ScriptedProvider:
    name = "scripted"
    model = "scripted-model"

    def __init__(self, contents: list[str]) -> None:
        self._contents = list(contents)

    async def complete(self, messages, *, temperature, max_tokens, tools=None, json_schema=None):
        del messages, temperature, max_tokens, tools, json_schema
        content = self._contents.pop(0)
        return ProviderResult(
            content=content,
            prompt_tokens=4,
            completion_tokens=2,
            model=self.model,
        )

    async def aclose(self) -> None:
        return None


def test_sliding_window_blocks_the_third_call() -> None:
    limiter = SlidingWindowLimiter(limit=1, window_seconds=60)
    asyncio.run(limiter.check("demo"))
    with pytest.raises(RateLimitExceeded):
        asyncio.run(limiter.check("demo"))


def test_extract_repairs_invalid_json_once() -> None:
    provider = ScriptedProvider(
        [
            "not json",
            '{"title": "Fix login", "priority": "high", "tags": ["auth"]}',
        ]
    )
    service = InferenceService(
        provider=provider,
        usage=UsageLedger(),
        settings=Settings(environment="test", provider="mock"),
    )
    response = asyncio.run(
        service.extract(
            "demo",
            StructuredRequest(text="Fix login urgently", schema_name="task"),
        )
    )
    assert response.data.priority == "high"
    assert response.usage.prompt_tokens == 8
    assert provider._contents == []


def test_extract_fails_when_both_attempts_are_invalid() -> None:
    service = InferenceService(
        provider=ScriptedProvider(["nope", "still nope"]),
        usage=UsageLedger(),
        settings=Settings(environment="test", provider="mock"),
    )
    with pytest.raises(SchemaMismatchError):
        asyncio.run(
            service.extract("demo", StructuredRequest(text="hello", schema_name="sentiment"))
        )


def test_production_refuses_the_default_secret() -> None:
    with pytest.raises(RuntimeError):
        ensure_production_secret(Settings(environment="prod", jwt_secret=DEV_JWT_SECRET))


def test_openai_provider_requires_a_key() -> None:
    settings = Settings(environment="test", provider="openai_compatible", openai_api_key="")
    with pytest.raises(RuntimeError):
        build_provider(settings)


def test_parse_ollama_tool_call() -> None:
    result = _parse_ollama(
        {
            "model": "llama3.2",
            "message": {
                "content": "",
                "tool_calls": [
                    {"function": {"name": "model_card", "arguments": {"model_name": "llama3.2"}}}
                ],
            },
            "prompt_eval_count": 11,
            "eval_count": 3,
        },
        [{"role": "user", "content": "card"}],
        "llama3.2",
    )
    assert result.model == "llama3.2"
    assert result.tool_calls[0].name == "model_card"
    assert result.tool_calls[0].arguments == {"model_name": "llama3.2"}
    assert result.prompt_tokens == 11


def test_parse_openai_string_arguments() -> None:
    result = _parse_openai(
        {
            "model": "llama-3.1-8b-instant",
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "estimate_tokens",
                                    "arguments": '{"text": "hi"}',
                                }
                            }
                        ],
                    }
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 1},
        },
        [{"role": "user", "content": "hi"}],
        "fallback",
    )
    assert result.tool_calls[0].arguments == {"text": "hi"}
    assert result.completion_tokens == 1
