import json

import pytest

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


@pytest.mark.parametrize(
    ("status_code", "expected_status"),
    [(429, 429), (403, 502), (500, 502)],
)
def test_artifact_provider_http_failures_are_bounded_and_do_not_leak_body(
    monkeypatch, capsys, status_code, expected_status
):
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret")

    class FakeResponse:
        def __init__(self):
            self.status_code = status_code

        def json(self):
            return {"error": {"message": "sensitive-provider-detail test-secret"}}

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

    assert response.status_code == expected_status
    assert "test-secret" not in response.text
    assert "sensitive-provider-detail" not in capsys.readouterr().out


@pytest.mark.parametrize(
    ("exception", "expected_status"),
    [
        (httpx.ReadTimeout("test-secret"), 504),
        (httpx.ConnectError("test-secret"), 502),
    ],
)
def test_artifact_provider_transport_failures_are_sanitized(
    monkeypatch, exception, expected_status
):
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret")

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            raise exception

    monkeypatch.setattr(artifacts.httpx, "AsyncClient", FakeClient)
    response = client.post(
        "/api/artifacts",
        json={"task": "Create a simple addition function and pytest cases."},
    )

    assert response.status_code == expected_status
    assert "test-secret" not in response.text
