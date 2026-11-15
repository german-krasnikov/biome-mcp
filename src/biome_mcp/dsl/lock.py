"""Content-lock verification for generated files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_lock(lock_path: Path) -> list[str]:
    """Return list of mismatched entries. Empty = all OK."""
    if not lock_path.exists():
        return ["lock file not found"]
    base = lock_path.parent
    entries = json.loads(lock_path.read_text(encoding="utf-8"))
    errors = []
    for entry in entries:
        target = base / entry["target"]
        if not target.exists():
            errors.append(f"missing: {entry['target']}")
            continue
        actual = compute_sha256(target)
        if actual != entry["sha256"]:
            expected = entry["sha256"][:12]
            errors.append(f"stale: {entry['target']} (expected {expected}…, got {actual[:12]}…)")
    return errors


def create_lock(entries: list[dict], lock_path: Path) -> None:
    """Write content-lock.json from list of {source, target, sha256}."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
