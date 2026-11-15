"""S7: content-lock verification."""
from __future__ import annotations

from pathlib import Path

from biome_mcp.dsl.lock import compute_sha256, create_lock, verify_lock


def test_s7_verify_ok(tmp_path: Path) -> None:
    target = tmp_path / "gen" / "out.py"
    target.parent.mkdir()
    target.write_text("hello", encoding="utf-8")
    sha = compute_sha256(target)

    lock_path = tmp_path / "content-lock.json"
    create_lock(
        [{"source": "tools.biome", "target": "gen/out.py", "sha256": sha}],
        lock_path,
    )
    assert verify_lock(lock_path) == []


def test_s7_verify_stale(tmp_path: Path) -> None:
    target = tmp_path / "gen" / "out.py"
    target.parent.mkdir()
    target.write_text("original", encoding="utf-8")
    sha = compute_sha256(target)

    lock_path = tmp_path / "content-lock.json"
    create_lock(
        [{"source": "tools.biome", "target": "gen/out.py", "sha256": sha}],
        lock_path,
    )

    target.write_text("modified by hand", encoding="utf-8")
    errors = verify_lock(lock_path)
    assert len(errors) == 1
    assert "stale" in errors[0]


def test_s7_verify_missing_target(tmp_path: Path) -> None:
    lock_path = tmp_path / "content-lock.json"
    create_lock(
        [{"source": "tools.biome", "target": "gen/missing.py", "sha256": "abc"}],
        lock_path,
    )
    errors = verify_lock(lock_path)
    assert len(errors) == 1
    assert "missing" in errors[0]


def test_s7_verify_no_lock_file(tmp_path: Path) -> None:
    errors = verify_lock(tmp_path / "nonexistent.json")
    assert len(errors) == 1
    assert "not found" in errors[0]
