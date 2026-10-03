import os

os.environ["PROVIDER"] = "mock"
os.environ["JWT_SECRET"] = "test-secret-must-be-32-bytes-min"
os.environ["DEMO_USERNAME"] = "demo"
os.environ["DEMO_PASSWORD"] = "demo-pass"
os.environ["ENVIRONMENT"] = "test"
os.environ["RATE_LIMIT_REQUESTS"] = "100"
os.environ["LOG_LEVEL"] = "WARNING"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.config import get_settings

    get_settings.cache_clear()
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_header(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/v1/auth/token",
        json={"username": "demo", "password": "demo-pass"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
