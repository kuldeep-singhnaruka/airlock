from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_JWT_SECRET = "dev-only-change-me-use-32-bytes-or-more"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "airlock"
    environment: Literal["local", "test", "prod"] = "local"
    log_level: str = "INFO"

    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=60, ge=1, le=24 * 60)

    demo_username: str = "demo"
    demo_password: str = "demo-pass"

    provider: Literal["mock", "ollama", "openai_compatible"] = "mock"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"
    openai_base_url: str = "https://api.groq.com/openai/v1"
    openai_api_key: str = ""
    openai_model: str = "llama-3.1-8b-instant"
    request_timeout_seconds: float = Field(default=60, gt=0, le=180)

    rate_limit_requests: int = Field(default=30, ge=1, le=1000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    max_tool_rounds: int = Field(default=3, ge=1, le=6)


def ensure_production_secret(settings: Settings) -> None:
    if settings.environment == "prod" and settings.jwt_secret == DEV_JWT_SECRET:
        raise RuntimeError("Set JWT_SECRET when ENVIRONMENT=prod.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
