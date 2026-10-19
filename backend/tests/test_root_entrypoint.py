from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


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

    paths = {route.path for route in module.app.routes}
    assert "/api/artifacts" in paths, paths
