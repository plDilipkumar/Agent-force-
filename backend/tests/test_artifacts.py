import json

from fastapi.testclient import TestClient

from app import artifacts, main


client = TestClient(main.app)


def test_artifact_generation_requires_real_provider_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    response = client.post(
        "/api/artifacts",
        json={"task": "Create a simple addition function and pytest cases."},
    )

    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]


def test_artifact_request_is_bounded():
    response = client.post(
        "/api/artifacts",
        json={"task": "valid task description", "context": "x" * 1501},
    )

    assert response.status_code == 422


def test_artifact_generation_returns_unexecuted_reviewable_files(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")

    generated = {
        "filename": "addition.py",
        "code": "def add(a, b):\n    return a + b\n",
        "test_filename": "test_addition.py",
        "test_code": "from addition import add\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    }

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "candidates": [
                    {"content": {"parts": [{"text": json.dumps(generated)}]}}
                ]
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers, json):
            assert headers["x-goog-api-key"] == "test-secret"
            assert "gemini-test:generateContent" in url
            return FakeResponse()

    monkeypatch.setattr(artifacts.httpx, "AsyncClient", FakeClient)

    response = client.post(
        "/api/artifacts",
        json={"task": "Create a simple addition function and pytest cases."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "addition.py"
    assert body["test_filename"] == "test_addition.py"
    assert body["verification_status"] == "not_executed"
    assert "not been executed" in body["safety_notice"]
    assert "test-secret" not in response.text


def test_artifact_rejects_unsafe_generated_filename(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret")

    generated = {
        "filename": "../leak.py",
        "code": "print('x')",
        "test_filename": "test_safe.py",
        "test_code": "def test_ok():\n    assert True",
    }

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "candidates": [
                    {"content": {"parts": [{"text": json.dumps(generated)}]}}
                ]
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(artifacts.httpx, "AsyncClient", FakeClient)

    response = client.post(
        "/api/artifacts",
        json={"task": "Create a simple addition function and pytest cases."},
    )

    assert response.status_code == 502
    assert "unsafe artifact filename" in response.json()["detail"]
