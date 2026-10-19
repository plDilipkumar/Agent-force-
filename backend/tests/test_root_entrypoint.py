from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def test_render_root_entrypoint_imports_artifact_route(monkeypatch):
    """Load the same root app.main module Render targets with uvicorn app.main:app."""
    repository_root = Path(__file__).resolve().parents[2]
    root_entrypoint = repository_root / "app" / "main.py"
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.syspath_prepend(str(repository_root))

    spec = importlib.util.spec_from_file_location(
        "agentforge_render_root_entrypoint", root_entrypoint
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Exercise the route instead of reading .path from lazy router wrappers.
    response = TestClient(module.app).post("/api/artifacts", json={})
    assert response.status_code == 422, response.text
