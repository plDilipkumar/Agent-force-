from __future__ import annotations

import base64

import pytest

from sandbox.validate_artifacts import materialize_artifacts


def enc(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def test_materializes_valid_bounded_source_and_test_pair(tmp_path):
    output = tmp_path / "artifacts"
    source = b"def add(a, b):\n    return a + b\n"
    test = b"from solution import add\ndef test_add():\n    assert add(2, 3) == 5\n"

    result = materialize_artifacts(
        "solution.py", enc(source), "test_solution.py", enc(test), output
    )

    assert result == output
    assert (output / "solution.py").read_bytes() == source
    assert (output / "test_solution.py").read_bytes() == test


@pytest.mark.parametrize("filename", ["../solution.py", "/tmp/solution.py", "bad-name.py", "x.py/evil"])
def test_rejects_unsafe_source_filename(tmp_path, filename):
    with pytest.raises(ValueError, match="source filename"):
        materialize_artifacts(
            filename, enc(b"print(1)"), "test_solution.py", enc(b"def test_ok(): pass"),
            tmp_path / "artifacts",
        )


@pytest.mark.parametrize("filename", ["solution.py", "../test_solution.py", "test-bad.py", "test_x.py/evil"])
def test_rejects_unsafe_test_filename(tmp_path, filename):
    with pytest.raises(ValueError, match="test filename"):
        materialize_artifacts(
            "solution.py", enc(b"print(1)"), filename, enc(b"def test_ok(): pass"),
            tmp_path / "artifacts",
        )


def test_rejects_invalid_base64_without_creating_output(tmp_path):
    output = tmp_path / "artifacts"
    with pytest.raises(ValueError, match="invalid base64"):
        materialize_artifacts(
            "solution.py", "not base64!", "test_solution.py", enc(b"def test_ok(): pass"), output
        )
    assert not output.exists()


def test_rejects_empty_or_oversized_artifact(tmp_path):
    with pytest.raises(ValueError, match="artifact size"):
        materialize_artifacts(
            "solution.py", enc(b""), "test_solution.py", enc(b"def test_ok(): pass"),
            tmp_path / "empty",
        )
    with pytest.raises(ValueError, match="artifact size"):
        materialize_artifacts(
            "solution.py", enc(b"x" * 12_001), "test_solution.py", enc(b"def test_ok(): pass"),
            tmp_path / "large",
        )


def test_rejects_nul_byte(tmp_path):
    with pytest.raises(ValueError, match="NUL byte"):
        materialize_artifacts(
            "solution.py", enc(b"print(\x00)"), "test_solution.py", enc(b"def test_ok(): pass"),
            tmp_path / "artifacts",
        )


def test_rejects_identical_source_and_test_names(tmp_path):
    with pytest.raises(ValueError, match="must differ"):
        materialize_artifacts(
            "test_solution.py", enc(b"print(1)"), "test_solution.py", enc(b"def test_ok(): pass"),
            tmp_path / "artifacts",
        )
