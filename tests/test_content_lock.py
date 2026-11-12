"""S19-S20: DSL content lock verification."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = ROOT / "dsl" / "content-lock.json"


def _digest(path: Path) -> str:
    data = re.sub(rb"\r\n?", b"\n", path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    return hashlib.sha256(data).hexdigest()


def test_content_lock_passes_clean_state():
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    for key, expected_hash in lock["files"].items():
        path = ROOT / key
        assert path.is_file(), f"locked file missing: {key}"
        assert _digest(path) == expected_hash, f"hash mismatch: {key}"


def test_content_lock_detects_modified_generated():
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    gen_key = next(
        k for k in lock["files"] if k.startswith("src/") and k.endswith(".py")
    )
    gen_path = ROOT / gen_key
    original = gen_path.read_bytes()
    try:
        gen_path.write_bytes(original + b"\n# tampered\n")
        assert _digest(gen_path) != lock["files"][gen_key]
    finally:
        gen_path.write_bytes(original)
