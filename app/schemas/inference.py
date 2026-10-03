from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class UsageStats(BaseModel):
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(min_length=1, max_length=20)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=256, ge=1, le=1024)
    enable_tools: bool = False


class ToolTrace(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: str


class ChatResponse(BaseModel):
    id: str
    model: str
    content: str
    usage: UsageStats
    tool_trace: list[ToolTrace] = Field(default_factory=list)


class TaskExtraction(BaseModel):
    """Structured task pulled out of free text."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=120)
    priority: Literal["low", "medium", "high"]
    tags: list[str] = Field(default_factory=list, max_length=8)


class SentimentExtraction(BaseModel):
    """Structured sentiment pulled out of free text."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    label: Literal["positive", "neutral", "negative"]
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1, max_length=400)


class StructuredRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(min_length=1, max_length=8000)
    schema_name: Literal["task", "sentiment"] = "task"


class StructuredResponse(BaseModel):
    id: str
    schema_name: Literal["task", "sentiment"]
    data: TaskExtraction | SentimentExtraction
    usage: UsageStats
    model: str


SCHEMA_MODELS: dict[str, type[TaskExtraction] | type[SentimentExtraction]] = {
    "task": TaskExtraction,
    "sentiment": SentimentExtraction,
}
