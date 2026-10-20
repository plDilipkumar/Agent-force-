from fastapi.testclient import TestClient

from app.main import app
from app import providers

client = TestClient(app)


def test_chat_uses_gemini_as_default_provider(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "configured-test-key")
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "configured-openrouter-key")

    async def fake_request(provider, prompt, schema):
        assert provider == "gemini"
        assert schema is None
        assert "What is an API?" in prompt
        return "An API lets software systems communicate.", "Google Gemini (test-model)"

    monkeypatch.setattr(providers, "_request", fake_request)
    response = client.post("/api/chat", json={"message": "What is an API?"})

    assert response.status_code == 200
    assert response.json()["reply"] == "An API lets software systems communicate."
    assert response.json()["provider"] == "Google Gemini (test-model)"


def test_chat_does_not_silently_fallback_when_gemini_times_out(monkeypatch):
    import httpx

    monkeypatch.setenv("GEMINI_API_KEY", "configured-test-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "configured-openrouter-key")

    async def fake_request(provider, prompt, schema):
        assert provider == "gemini"
        raise httpx.ReadTimeout("private upstream details")

    monkeypatch.setattr(providers, "_request", fake_request)
    response = client.post("/api/chat", json={"message": "Give me a short answer"})

    assert response.status_code == 504
    assert "Gemini took too long" in response.json()["detail"]
    assert "private upstream details" not in response.text
    assert "openrouter" not in response.text.lower()


def test_chat_rejects_blank_message():
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 422


def test_chat_requires_gemini_configuration(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "configured-openrouter-key")
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 503
    assert "Gemini is not configured" in response.json()["detail"]
