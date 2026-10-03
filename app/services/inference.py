from uuid import uuid4

from pydantic import ValidationError

from app.config import Settings
from app.providers.base import ModelProvider
from app.providers.errors import ProviderError
from app.schemas.inference import (
    SCHEMA_MODELS,
    ChatRequest,
    ChatResponse,
    StructuredRequest,
    StructuredResponse,
    ToolTrace,
    UsageStats,
)
from app.services.errors import ModelBackendError, SchemaMismatchError, ToolLoopError
from app.services.prompts import CHAT_SYSTEM_PROMPT, structured_system_prompt
from app.services.tools import TOOL_SPECS, execute_tool
from app.services.usage import UsageLedger


def extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        fence = stripped.rfind("```")
        if fence >= 0:
            stripped = stripped[:fence]
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return stripped[start : end + 1]
    return stripped.strip()


class InferenceService:
    def __init__(self, provider: ModelProvider, usage: UsageLedger, settings: Settings) -> None:
        self._provider = provider
        self._usage = usage
        self._settings = settings

    async def chat(self, username: str, request: ChatRequest) -> ChatResponse:
        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        messages.extend(message.model_dump() for message in request.messages)
        tools = TOOL_SPECS if request.enable_tools else None
        traces: list[ToolTrace] = []
        prompt_tokens = 0
        completion_tokens = 0

        for _ in range(self._settings.max_tool_rounds):
            result = await self._complete(
                messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=tools,
            )
            prompt_tokens += result.prompt_tokens
            completion_tokens += result.completion_tokens
            if not result.tool_calls:
                await self._usage.record(username, prompt_tokens, completion_tokens)
                return ChatResponse(
                    id=f"chat_{uuid4().hex}",
                    model=result.model,
                    content=result.content,
                    usage=_usage(prompt_tokens, completion_tokens),
                    tool_trace=traces,
                )
            for call in result.tool_calls:
                output = execute_tool(call.name, call.arguments)
                traces.append(ToolTrace(name=call.name, arguments=call.arguments, result=output))
                messages.append(
                    {"role": "assistant", "content": result.content or f"Calling {call.name}"}
                )
                messages.append(
                    {"role": "user", "content": f"Tool result for {call.name}: {output}"}
                )
            tools = None

        raise ToolLoopError("Tool loop did not finish.")

    async def extract(self, username: str, request: StructuredRequest) -> StructuredResponse:
        schema_model = SCHEMA_MODELS[request.schema_name]
        schema = schema_model.model_json_schema()
        messages = [
            {
                "role": "system",
                "content": structured_system_prompt(request.schema_name, schema),
            },
            {"role": "user", "content": request.text},
        ]
        prompt_tokens = 0
        completion_tokens = 0

        for _ in range(2):
            result = await self._complete(
                messages,
                temperature=0,
                max_tokens=400,
                json_schema=schema,
            )
            prompt_tokens += result.prompt_tokens
            completion_tokens += result.completion_tokens
            try:
                data = schema_model.model_validate_json(extract_json_object(result.content))
            except ValidationError as exc:
                messages.append({"role": "assistant", "content": result.content or "invalid"})
                messages.append(
                    {
                        "role": "user",
                        "content": f"Validation failed: {exc}. Return only corrected JSON.",
                    }
                )
                continue
            await self._usage.record(username, prompt_tokens, completion_tokens)
            return StructuredResponse(
                id=f"ext_{uuid4().hex}",
                schema_name=request.schema_name,
                data=data,
                usage=_usage(prompt_tokens, completion_tokens),
                model=result.model,
            )

        raise SchemaMismatchError("Model output did not match the schema.")

    async def _complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        tools: list[dict] | None = None,
        json_schema: dict | None = None,
    ):
        try:
            return await self._provider.complete(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                json_schema=json_schema,
            )
        except ProviderError as exc:
            raise ModelBackendError("Model provider request failed.") from exc


def _usage(prompt_tokens: int, completion_tokens: int) -> UsageStats:
    return UsageStats(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
