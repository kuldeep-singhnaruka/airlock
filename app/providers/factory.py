from app.config import Settings
from app.providers.base import ModelProvider
from app.providers.mock import MockProvider
from app.providers.ollama import OllamaProvider
from app.providers.openai_compatible import OpenAICompatibleProvider


def build_provider(settings: Settings) -> ModelProvider:
    if settings.provider == "mock":
        return MockProvider()
    if settings.provider == "ollama":
        return OllamaProvider(settings)
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required when PROVIDER=openai_compatible.")
    return OpenAICompatibleProvider(settings)
