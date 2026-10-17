import app.main as main
from fastapi.testclient import TestClient

client = TestClient(main.app)


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, response: FakeResponse):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return self.response


def request_with_provider_error(monkeypatch, status_code: int, payload: dict):
    monkeypatch.setattr(main, "API_KEY", "test-only-not-a-real-key")
    fake = FakeResponse(status_code, payload)
    monkeypatch.setattr(
        main.httpx,
        "AsyncClient",
        lambda *args, **kwargs: FakeAsyncClient(fake),
    )
    return client.post(
        "/api/run",
        json={"task": "Create a reliable upload API with clear error handling"},
    )


def test_gemini_rate_limit_is_reported_as_429(monkeypatch):
    response = request_with_provider_error(
        monkeypatch,
        429,
        {"error": {"message": "quota exceeded", "status": "RESOURCE_EXHAUSTED"}},
    )
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


def test_gemini_permission_error_does_not_expose_key(monkeypatch):
    response = request_with_provider_error(
        monkeypatch,
        403,
        {"error": {"message": "permission denied", "status": "PERMISSION_DENIED"}},
    )
    assert response.status_code == 502
    assert "test-only-not-a-real-key" not in response.text


def test_unknown_gemini_provider_error_is_safely_wrapped(monkeypatch):
    response = request_with_provider_error(
        monkeypatch,
        404,
        {"error": {"message": "model not found", "status": "NOT_FOUND"}},
    )
    assert response.status_code == 502
    assert "test-only-not-a-real-key" not in response.text
