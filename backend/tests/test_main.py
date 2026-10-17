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
