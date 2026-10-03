from fastapi.testclient import TestClient


def test_login_and_reject_bad_password(client: TestClient) -> None:
    bad = client.post("/v1/auth/token", json={"username": "demo", "password": "wrong"})
    assert bad.status_code == 401

    good = client.post("/v1/auth/token", json={"username": "demo", "password": "demo-pass"})
    body = good.json()
    assert good.status_code == 200
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600


def test_protected_routes_require_jwt(client: TestClient) -> None:
    assert (
        client.post("/v1/chat", json={"messages": [{"role": "user", "content": "hi"}]}).status_code
        == 401
    )
    assert client.get("/v1/usage").status_code == 401
    forged = client.get("/v1/usage", headers={"Authorization": "Bearer not-a-token"})
    assert forged.status_code == 401


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "mock"
    assert body["model"] == "mock-model"
    assert "x-request-id" in response.headers
