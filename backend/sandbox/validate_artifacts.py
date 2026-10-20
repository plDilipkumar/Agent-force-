from __future__ import annotations

import base64
import binascii
import os
import re
from pathlib import Path

_SOURCE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}\.py$")
_TEST_NAME = re.compile(r"^test_[A-Za-z0-9_]{1,58}\.py$")
_MAX_BYTES = 12_000


def _decode_bounded(value: str, label: str) -> bytes:
    try:
        data = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError(f"Rejected invalid base64 input: {label}") from None
    if not data or len(data) > _MAX_BYTES:
        raise ValueError(f"Rejected artifact size for {label}")
    if b"\x00" in data:
        raise ValueError(f"Rejected NUL byte in {label}")
    return data


def materialize_artifacts(
    source_filename: str,
    source_b64: str,
    test_filename: str,
    test_b64: str,
    output_dir: str | Path,
) -> Path:
    """Validate two bounded Python files and write them into a fresh directory."""
    if not _SOURCE_NAME.fullmatch(source_filename) or ".." in source_filename:
        raise ValueError("Rejected source filename")
    if not _TEST_NAME.fullmatch(test_filename) or ".." in test_filename:
        raise ValueError("Rejected test filename")
    if source_filename == test_filename:
        raise ValueError("Source and test filenames must differ")

    source = _decode_bounded(source_b64, "SOURCE_B64")
    tests = _decode_bounded(test_b64, "TEST_B64")
    output = Path(output_dir)
    output.mkdir(mode=0o755, parents=True, exist_ok=False)
    (output / source_filename).write_bytes(source)
    (output / test_filename).write_bytes(tests)
    return output


def main() -> int:
    try:
        materialize_artifacts(
            os.environ["SOURCE_FILENAME"],
            os.environ["SOURCE_B64"],
            os.environ["TEST_FILENAME"],
            os.environ["TEST_B64"],
            os.environ["OUTPUT_DIR"],
        )
    except (KeyError, ValueError, OSError) as exc:
        # Only bounded validation errors are printed; artifact contents are never logged.
        print(str(exc) or "Artifact validation failed")
        return 1
    print("Validated two bounded Python files; source contents are not logged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
