from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_is_available():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_run_uses_demo_without_api_key(monkeypatch):
    import app.main as main
    monkeypatch.setattr(main, "API_KEY", "")
    response = client.post("/api/run", json={
        "task":"Create a reliable file upload API",
        "context":"Support PDFs under 10 MB",
        "stack":"FastAPI + React",
        "mode":"balanced"
    })
    assert response.status_code == 200
    body = response.json()
    assert body["provider"].startswith("Deterministic demo")
    assert body["tasks"]
    assert "not executed" in body["notice"]

def test_short_task_is_rejected():
    response = client.post("/api/run", json={"task":"too short"})
    assert response.status_code == 422

def test_cors_preflight_allows_local_frontend_post():
    response = client.options(
        "/api/run",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "").split(", ")
    assert "content-type" in response.headers.get("access-control-allow-headers", "").lower()

def test_cors_preflight_does_not_allow_unknown_origin():
    response = client.options(
        "/api/run",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 400
    assert response.headers.get("access-control-allow-origin") is None
