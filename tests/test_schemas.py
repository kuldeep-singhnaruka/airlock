import pytest
from pydantic import ValidationError

from app.schemas.auth import TokenRequest
from app.schemas.inference import ChatRequest, SentimentExtraction, TaskExtraction
from app.services.inference import extract_json_object


def test_token_request_strips_and_forbids_extra() -> None:
    parsed = TokenRequest.model_validate({"username": " demo ", "password": "secret"})
    assert parsed.username == "demo"
    with pytest.raises(ValidationError):
        TokenRequest.model_validate({"username": "demo", "password": "secret", "role": "admin"})


def test_chat_request_bounds() -> None:
    with pytest.raises(ValidationError):
        ChatRequest.model_validate({"messages": [], "max_tokens": 1})
    with pytest.raises(ValidationError):
        ChatRequest.model_validate(
            {"messages": [{"role": "user", "content": "hi"}], "max_tokens": 5000}
        )


def test_extraction_models_reject_bad_enums() -> None:
    with pytest.raises(ValidationError):
        TaskExtraction.model_validate({"title": "Ship it", "priority": "urgent", "tags": []})
    with pytest.raises(ValidationError):
        SentimentExtraction.model_validate(
            {"label": "positive", "confidence": 1.4, "rationale": "too sure"}
        )


def test_extract_json_object_strips_fences() -> None:
    raw = '```json\n{"title": "Ship it", "priority": "low", "tags": []}\n```'
    parsed = TaskExtraction.model_validate_json(extract_json_object(raw))
    assert parsed.priority == "low"
