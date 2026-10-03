from fastapi.testclient import TestClient

from app.services.rate_limit import SlidingWindowLimiter


def test_chat_and_usage(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.post(
        "/v1/chat",
        headers=auth_header,
        json={"messages": [{"role": "user", "content": "Say hello"}], "temperature": 0.2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "Mock reply: Say hello"
    assert (
        body["usage"]["total_tokens"]
        == body["usage"]["prompt_tokens"] + body["usage"]["completion_tokens"]
    )
    assert body["tool_trace"] == []

    usage = client.get("/v1/usage", headers=auth_header)
    assert usage.status_code == 200
    assert usage.json()["requests"] == 1
    assert usage.json()["username"] == "demo"


def test_tool_call_round_trip(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.post(
        "/v1/chat",
        headers=auth_header,
        json={
            "messages": [{"role": "user", "content": "How many tokens are in hello airlock?"}],
            "enable_tools": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tool_trace"][0]["name"] == "estimate_tokens"
    assert "estimated_tokens" in body["tool_trace"][0]["result"]
    assert body["content"].startswith("Tool finished.")


def test_structured_task_and_sentiment(client: TestClient, auth_header: dict[str, str]) -> None:
    task = client.post(
        "/v1/extract",
        headers=auth_header,
        json={"text": "Please fix the login bug today, this is urgent", "schema_name": "task"},
    )
    assert task.status_code == 200
    task_body = task.json()
    assert task_body["data"]["priority"] == "high"
    assert task_body["data"]["tags"] == ["extracted"]

    sentiment = client.post(
        "/v1/extract",
        headers=auth_header,
        json={"text": "I love this API", "schema_name": "sentiment"},
    )
    assert sentiment.status_code == 200
    assert sentiment.json()["data"]["label"] == "positive"


def test_schema_rejects_unknown_fields(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.post(
        "/v1/chat",
        headers=auth_header,
        json={"messages": [{"role": "user", "content": "hi"}], "nope": True},
    )
    assert response.status_code == 422

    hot = client.post(
        "/v1/chat",
        headers=auth_header,
        json={"messages": [{"role": "user", "content": "hi"}], "temperature": 3},
    )
    assert hot.status_code == 422


def test_rate_limit(client: TestClient, auth_header: dict[str, str]) -> None:
    client.app.state.limiter = SlidingWindowLimiter(limit=2, window_seconds=60)
    payload = {"messages": [{"role": "user", "content": "hi"}]}
    assert client.post("/v1/chat", headers=auth_header, json=payload).status_code == 200
    assert client.post("/v1/chat", headers=auth_header, json=payload).status_code == 200
    blocked = client.post("/v1/chat", headers=auth_header, json=payload)
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"] == "60"


def test_models_lists_tools(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.get("/v1/models", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert "estimate_tokens" in body["tools"]
    assert "model_card" in body["tools"]
