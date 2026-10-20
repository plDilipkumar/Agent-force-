import asyncio
import json

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
        if provider == "openrouter":
            raise httpx.ReadTimeout("do not leak this")
        return '{"summary":"ok"}', "Cloudflare Workers AI (test-model)"

    monkeypatch.setattr(providers, "_request", fake_request)
    text, name = asyncio.run(providers.generate_text("task", {"type": "OBJECT"}))
    assert text == '{"summary":"ok"}'
    assert name.startswith("Cloudflare Workers AI")
    assert calls == ["openrouter", "cloudflare"]


def test_no_provider_configured_is_explicit(monkeypatch):
    for key in ("GEMINI_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(providers.ProviderUnavailable, match="generation providers")
        asyncio.run(providers.generate_text("task"))


def test_provider_failover_after_malformed_json(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "cf-test")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "account-test")
    calls = []

    async def fake_request(provider, prompt, schema):
        calls.append(provider)
        if provider == "openrouter":
            return "not json", "OpenRouter (test)"
        return '{"summary":"ok"}', "Cloudflare Workers AI (test)"

    monkeypatch.setattr(providers, "_request", fake_request)
    text, name = asyncio.run(providers.generate_text("task", {"type": "OBJECT"}))
    assert text == '{"summary":"ok"}'
    assert name.startswith("Cloudflare")
    assert calls == ["openrouter", "cloudflare"]


def test_multi_agent_merges_independent_provider_outputs(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "c")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "a")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o")
    calls = []

    async def fake_request(provider, prompt, schema):
        calls.append((provider, prompt))
        payload = {
            "summary": provider + " summary",
            "spec": [provider + " spec"],
            "tasks": [{"title": provider + " task", "description": "detail", "priority": "P1", "estimate": "1h"}],
            "decisions": [{"title": provider + " decision", "rationale": "reason"}],
            "risks": [provider + " risk"],
            "verification": [provider + " check"],
            "assumptions": [provider + " assumption"],
        }
        return json.dumps(payload), provider + " provider"

    monkeypatch.setattr(providers, "_request", fake_request)
    text, label = asyncio.run(providers.generate_multi_agent_text("base prompt", {"type": "OBJECT"}))
    merged = json.loads(text)
    assert len(calls) == 3
    assert {provider for provider, _ in calls} == {"openrouter", "cloudflare", "gemini"}
    assert all("Independent reviewer role:" in prompt for provider, prompt in calls if provider in {"openrouter", "cloudflare"})
    assert any("Review and improve" in prompt for provider, prompt in calls if provider == "gemini")
    assert len(merged["tasks"]) == 3
    assert len(merged["risks"]) == 3
    assert "Generation workers" in label
    assert "Gemini" in label and "cloudflare provider" in label and "openrouter provider" in label


def test_multi_agent_discards_invalid_worker_and_keeps_valid_result(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "c")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "a")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o")

    async def fake_request(provider, prompt, schema):
        if provider == "cloudflare":
            return json.dumps({"summary": "bad but incomplete"}), "Cloudflare"
        payload = {
            "summary": "valid summary", "spec": ["spec"],
            "tasks": [{"title": "task", "description": "detail", "priority": "P1", "estimate": "1h"}],
            "decisions": [{"title": "decision", "rationale": "reason"}],
            "risks": ["risk"], "verification": ["check"], "assumptions": ["assumption"],
        }
        return json.dumps(payload), "Cloudflare"

    monkeypatch.setattr(providers, "_request", fake_request)
    text, label = asyncio.run(providers.generate_multi_agent_text("base", {"type": "OBJECT"}))
    merged = json.loads(text)
    assert merged["summary"] == "valid summary"
    assert len(merged["tasks"]) == 1
    assert "partial generation failure: cloudflare: invalid response" in label


def test_extract_openrouter_text():
    assert providers._extract_text("openrouter", {"choices":[{"message":{"content":"{}"}}]}) == "{}"


def test_extract_cloudflare_text():
    assert providers._extract_text("cloudflare", {"result":{"response":"{}"}}) == "{}"


def test_multi_agent_discards_worker_with_invalid_priority(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "c")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "a")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o")

    async def fake_request(provider, prompt, schema):
        payload = {
            "summary": "invalid priority", "spec": ["spec"],
            "tasks": [{"title": "task", "description": "detail", "priority": "urgent", "estimate": "1h"}],
            "decisions": [{"title": "decision", "rationale": "reason"}],
            "risks": ["risk"], "verification": ["check"], "assumptions": ["assumption"],
        }
        return json.dumps(payload), "Gemini"

    monkeypatch.setattr(providers, "_request", fake_request)
    with pytest.raises(providers.ProviderUnavailable, match="generation workers failed"):
        asyncio.run(providers.generate_multi_agent_text("base", {"type": "OBJECT"}))


@pytest.mark.parametrize("status_code, expected_status", [(401, 502), (429, 429)])
def test_provider_http_failures_are_sanitized(monkeypatch, status_code, expected_status):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-test-key")
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-test-key")

    async def fake_request(provider, prompt, schema):
        raise RuntimeError("secret-test-key upstream detail", status_code)

    monkeypatch.setattr(providers, "_request", fake_request)
    with pytest.raises(providers.ProviderUnavailable) as caught:
        asyncio.run(providers.generate_text("task"))
    assert caught.value.status_code == expected_status
    assert "secret-test-key" not in str(caught.value)
    assert "upstream detail" not in str(caught.value)


def test_multi_agent_failure_logs_only_safe_provider_category(monkeypatch, capsys):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-test-key")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "c")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "a")
    monkeypatch.setenv("OPENROUTER_API_KEY", "o")

    async def fake_request(provider, prompt, schema):
        raise httpx.ReadTimeout("secret-test-key and private response detail")

    monkeypatch.setattr(providers, "_request", fake_request)
    with pytest.raises(providers.ProviderUnavailable):
        asyncio.run(providers.generate_multi_agent_text("task", {"type": "OBJECT"}))

    output = capsys.readouterr().out
    assert "provider=openrouter category=timeout" in output
    assert "secret-test-key" not in output
    assert "private response detail" not in output


@pytest.mark.parametrize("provider", ["cloudflare", "openrouter"])
def test_openai_style_providers_receive_json_constraints(monkeypatch, provider):
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "account-test")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "cloudflare-test-token")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-test-token")
    monkeypatch.setenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.1-8b-instruct-fp8")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/free")
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            if provider == "cloudflare":
                return {"result": {"response": '{"summary":"ok"}'}}
            return {"choices": [{"message": {"content": '{"summary":"ok"}'}}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers, json):
            captured["url"] = url
            captured["body"] = json
            return FakeResponse()

    monkeypatch.setattr(providers.httpx, "AsyncClient", FakeClient)
    schema = {
        "type": "OBJECT",
        "properties": {"summary": {"type": "STRING"}, "tasks": {"type": "ARRAY", "items": {"type": "STRING"}}},
        "required": ["summary", "tasks"],
    }
    text, _ = asyncio.run(providers._request(provider, "Plan the task", schema))

    assert text == '{"summary":"ok"}'
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert "Required JSON fields" in captured["body"]["messages"][0]["content"]
    assert "summary" in captured["body"]["messages"][0]["content"]
    assert captured["body"]["temperature"] == 0.1
    assert captured["body"]["max_tokens"] == 4096
