from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def test_health_reports_service_without_exposing_secrets():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "agentforge-api"
    assert "api_key" not in body
    assert "GEMINI_API_KEY" not in response.text


def test_run_rejects_task_that_is_too_short():
    response = client.post("/api/run", json={"task": "too short"})

    assert response.status_code == 422


def test_demo_mode_is_explicit_and_does_not_claim_tests_ran(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "")

    response = client.post(
        "/api/run",
        json={
            "task": "Create a reliable addition function with unit tests.",
            "stack": "Python + FastAPI",
            "mode": "balanced",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"].startswith("Deterministic demo")
    assert "not executed test results" in body["notice"]
    assert body["verification"]
    assert body["tasks"]
