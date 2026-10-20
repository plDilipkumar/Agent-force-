import asyncio
import json

import pytest

from app import providers


def _valid_plan():
    return {
        "summary": "valid summary",
        "spec": ["spec"],
        "tasks": [{"title": "task", "description": "detail", "priority": "P1", "estimate": "1h"}],
        "decisions": [{"title": "decision", "rationale": "reason"}],
        "risks": ["risk"],
        "verification": ["check"],
        "assumptions": ["assumption"],
    }


def _only_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


def test_multi_agent_retries_malformed_json_once(monkeypatch):
    _only_gemini(monkeypatch)
    calls = []

    async def fake_request(provider, prompt, schema):
        calls.append(prompt)
        if len(calls) == 1:
            return '{"summary": "truncated"', "Gemini"
        return json.dumps(_valid_plan()), "Gemini"

    monkeypatch.setattr(providers, "_request", fake_request)
    text, label = asyncio.run(providers.generate_multi_agent_text("base prompt", {"type": "OBJECT"}))

    assert len(calls) == 2
    assert "FORMAT RETRY" in calls[1]
    assert "truncated" not in calls[1]
    assert json.loads(text)["summary"] == "valid summary"
    assert "Gemini" in label


def test_multi_agent_malformed_json_retry_is_bounded(monkeypatch):
    _only_gemini(monkeypatch)
    calls = []

    async def fake_request(provider, prompt, schema):
        calls.append(prompt)
        return '{"summary": }', "Gemini"

    monkeypatch.setattr(providers, "_request", fake_request)
    with pytest.raises(providers.ProviderUnavailable, match="invalid response or provider error"):
        asyncio.run(providers.generate_multi_agent_text("base prompt", {"type": "OBJECT"}))

    assert len(calls) == 2
    assert "FORMAT RETRY" in calls[1]
