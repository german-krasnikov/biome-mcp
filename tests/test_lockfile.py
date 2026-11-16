"""Tests for biome_mcp.lockfile — platform-agnostic lock primitives."""
import os
import sys
from pathlib import Path

import pytest


# ── is_pid_alive ──────────────────────────────────────────────────────────────

def test_is_pid_alive_none_returns_false():
    from biome_mcp.lockfile import is_pid_alive
    assert is_pid_alive(None) is False


def test_is_pid_alive_self_returns_true():
    from biome_mcp.lockfile import is_pid_alive
    assert is_pid_alive(os.getpid()) is True


def test_is_pid_alive_dead_pid_returns_false():
    from biome_mcp.lockfile import is_pid_alive
    assert is_pid_alive(99999999) is False


# ── write_lock_metadata / read_lock_metadata ──────────────────────────────────

def test_read_lock_metadata_roundtrip(tmp_path):
    from biome_mcp.lockfile import write_lock_metadata, read_lock_metadata, _OPEN_FLAGS
    lock_file = tmp_path / "test.lock"
    fd = os.open(str(lock_file), _OPEN_FLAGS, 0o600)
    try:
        # write a PID line first (line 1), then metadata on line 2
        os.write(fd, b"12345\n")
        meta = {"ppid": 42, "port": 9500}
        write_lock_metadata(fd, meta)
        result = read_lock_metadata(fd)
        assert result == meta
    finally:
        os.close(fd)


def test_read_lock_metadata_absent_returns_none(tmp_path):
    from biome_mcp.lockfile import read_lock_metadata, _OPEN_FLAGS
    lock_file = tmp_path / "test.lock"
    fd = os.open(str(lock_file), _OPEN_FLAGS, 0o600)
    try:
        os.write(fd, b"12345\n")  # only PID line, no metadata
        result = read_lock_metadata(fd)
        assert result is None
    finally:
        os.close(fd)


# ── acquire_lock / release_lock ────────────────────────────────────────────────

def test_acquire_lock_creates_lock_file(tmp_path):
    from biome_mcp.lockfile import acquire_lock, release_lock
    fd = acquire_lock(tmp_path, port=9500)
    try:
        # file server-9500-{pid}.lock must exist
        lock_file = tmp_path / f"server-9500-{os.getpid()}.lock"
        assert lock_file.exists()
    finally:
        release_lock(fd)


def test_release_lock_removes_lock_file(tmp_path):
    from biome_mcp.lockfile import acquire_lock, release_lock
    fd = acquire_lock(tmp_path, port=9500)
    lock_file = tmp_path / f"server-9500-{os.getpid()}.lock"
    release_lock(fd)
    assert not lock_file.exists()


def test_acquire_lock_writes_metadata(tmp_path):
    from biome_mcp.lockfile import acquire_lock, release_lock, read_lock_metadata
    meta = {"ppid": os.getppid(), "port": 9500}
    fd = acquire_lock(tmp_path, port=9500, metadata=meta)
    try:
        result = read_lock_metadata(fd)
        assert result is not None
        assert result.get("port") == 9500
    finally:
        release_lock(fd)


@pytest.mark.skipif(sys.platform == "win32", reason="double-lock raises on POSIX only via flock")
def test_acquire_lock_same_pid_raises(tmp_path):
    from biome_mcp.lockfile import acquire_lock, release_lock
    fd = acquire_lock(tmp_path, port=9501)
    try:
        with pytest.raises(RuntimeError, match="already holds"):
            acquire_lock(tmp_path, port=9501)
    finally:
        release_lock(fd)


def test_acquire_lock_creates_dir_if_missing(tmp_path):
    from biome_mcp.lockfile import acquire_lock, release_lock
    new_dir = tmp_path / "nested" / "lock"
    fd = acquire_lock(new_dir, port=9500)
    try:
        assert new_dir.exists()
    finally:
        release_lock(fd)
