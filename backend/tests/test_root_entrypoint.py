from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_render_root_entrypoint_imports_artifact_route():
    """Mirror Render's root-directory command: uvicorn app.main:app."""
    repository_root = Path(__file__).resolve().parents[2]
    code = (
        "from app.main import app; "
        "paths = {route.path for route in app.routes}; "
        "assert '/api/artifacts' in paths, paths"
    )
    env = os.environ.copy()
    env.pop("GEMINI_API_KEY", None)
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repository_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, (
        "Root entrypoint failed to import/register /api/artifacts.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
