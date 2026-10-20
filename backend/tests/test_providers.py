import asyncio

import httpx
import pytest

from app import providers


def test_configured_providers_only_reports_complete_credentials(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "c")
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "o")
    assert providers.configured_providers() == ["gemini", "openrouter"]


def test_provider_failover_after_gemini_timeout(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "cf-test")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "account-test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
    calls = []

    async def fake_request(provider, prompt, schema):
        calls.append(provider)
        if provider == "gemini":
            raise httpx.ReadTimeout("do not leak this")
        return '{"summary":"ok"}', "Cloudflare Workers AI (test-model)"

    monkeypatch.setattr(providers, "_request", fake_request)
    text, name = asyncio.run(providers.generate_text("task", {"type": "OBJECT"}))
    assert text == '{"summary":"ok"}'
    assert name.startswith("Cloudflare Workers AI")
    assert calls == ["gemini", "cloudflare"]


def test_no_provider_configured_is_explicit(monkeypatch):
    for key in ("GEMINI_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(providers.ProviderUnavailable, match="GEMINI_API_KEY"):
        asyncio.run(providers.generate_text("task"))


def test_extract_openrouter_text():
    assert providers._extract_text("openrouter", {"choices":[{"message":{"content":"{}"}}]}) == "{}"


def test_extract_cloudflare_text():
    assert providers._extract_text("cloudflare", {"result":{"response":"{}"}}) == "{}"
