from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    provider: str
    model: str
    version: str


class UsageResponse(BaseModel):
    username: str
    requests: int = Field(ge=0)
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class ModelInfo(BaseModel):
    provider: str
    model: str
    tools: list[str]
