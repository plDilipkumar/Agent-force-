from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_render_root_entrypoint_registers_artifact_route():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.main import app; assert any(route.path == '/api/artifacts' for route in app.routes)",
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
