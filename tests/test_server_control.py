"""Tests for biome_mcp.server_control — list and stop server processes.

Generic PID-lockfile monitoring: lock_dir is always required (no engine-specific
default directory), filenames follow server-{port}-{pid}.lock.
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

# ── helpers ───────────────────────────────────────────────────────────────────

def _make_lockfile(lock_dir: Path, port: int, pid: int) -> Path:
    f = lock_dir / f"server-{port}-{pid}.lock"
    f.write_text(f"{pid}\n", encoding="utf-8")
    return f


def _make_lockfile_with_meta(lock_dir: Path, port: int, pid: int, meta: dict) -> Path:
    f = lock_dir / f"server-{port}-{pid}.lock"
    f.write_text(f"{pid}\n{json.dumps(meta)}\n", encoding="utf-8")
    return f


# ── list_servers ──────────────────────────────────────────────────────────────

def test_list_servers_empty_when_no_lock_dir(tmp_path):
    from biome_mcp.server_control import list_servers
    result = list_servers(lock_dir=tmp_path / "nonexistent")
    assert result == []


def test_list_servers_filters_dead_pids(tmp_path, monkeypatch):
    from biome_mcp import server_control
    from biome_mcp.server_control import list_servers

    dead_pid = 99999
    live_pid = os.getpid()
    _make_lockfile(tmp_path, 9500, dead_pid)
    _make_lockfile(tmp_path, 9500, live_pid)

    monkeypatch.setattr(server_control, "is_pid_alive",
                        lambda pid: pid == live_pid)

    result = list_servers(lock_dir=tmp_path)
    pids = [e["pid"] for e in result]
    assert live_pid in pids
    assert dead_pid not in pids


def test_list_servers_parses_port_and_pid(tmp_path, monkeypatch):
    from biome_mcp import server_control
    from biome_mcp.server_control import list_servers

    _make_lockfile(tmp_path, 9515, 12345)
    monkeypatch.setattr(server_control, "is_pid_alive", lambda pid: pid == 12345)

    result = list_servers(lock_dir=tmp_path)
    assert len(result) == 1
    assert result[0]["port"] == 9515
    assert result[0]["pid"] == 12345
    assert result[0]["lock_path"] == tmp_path / "server-9515-12345.lock"


def test_list_servers_skips_malformed_filenames(tmp_path, monkeypatch):
    from biome_mcp import server_control
    from biome_mcp.server_control import list_servers

    (tmp_path / "server-abc-xyz.lock").write_text("", encoding="utf-8")
    (tmp_path / "random.lock").write_text("", encoding="utf-8")
    monkeypatch.setattr(server_control, "is_pid_alive", lambda pid: True)

    result = list_servers(lock_dir=tmp_path)
    assert result == []


def test_list_servers_multiple_ports(tmp_path, monkeypatch):
    from biome_mcp import server_control
    from biome_mcp.server_control import list_servers

    _make_lockfile(tmp_path, 9515, 11)
    _make_lockfile(tmp_path, 9602, 22)
    monkeypatch.setattr(server_control, "is_pid_alive", lambda pid: True)

    result = list_servers(lock_dir=tmp_path)
    ports = {e["port"] for e in result}
    assert ports == {9515, 9602}
    assert len(result) == 2


# ── stop_server ───────────────────────────────────────────────────────────────

def test_stop_server_returns_false_when_no_server(tmp_path):
    from biome_mcp.server_control import stop_server
    result = stop_server(port=9500, lock_dir=tmp_path)
    assert result is False


def test_stop_server_returns_false_for_port_zero(tmp_path):
    from biome_mcp.server_control import stop_server
    calls = []
    result = stop_server(port=0, lock_dir=tmp_path, _kill_fn=lambda *a: calls.append(a))
    assert result is False
    assert calls == []


def test_stop_server_sends_sigterm_on_posix(tmp_path, monkeypatch):
    if sys.platform == "win32":
        pytest.skip("POSIX-only test")

    from biome_mcp import server_control
    from biome_mcp.server_control import stop_server

    pid = 54321
    _make_lockfile(tmp_path, 9500, pid)

    kill_calls = []

    def mock_kill(p, sig):
        kill_calls.append((p, sig))
        for f in tmp_path.glob(f"server-9500-{pid}.lock"):
            f.unlink()

    def mock_alive(p):
        return (tmp_path / f"server-9500-{p}.lock").exists()

    monkeypatch.setattr(server_control, "is_pid_alive", mock_alive)

    result = stop_server(port=9500, lock_dir=tmp_path, _kill_fn=mock_kill)

    assert (pid, signal.SIGTERM) in kill_calls
    assert result is True


def test_stop_server_sigkill_fallback_on_timeout(tmp_path, monkeypatch):
    if sys.platform == "win32":
        pytest.skip("POSIX-only test")

    from biome_mcp import server_control
    from biome_mcp.server_control import stop_server

    pid = 54321
    _make_lockfile(tmp_path, 9500, pid)

    kill_calls = []

    def mock_kill(p, sig):
        kill_calls.append((p, sig))
        # Do NOT remove lockfile — simulate stuck process

    monkeypatch.setattr(server_control, "is_pid_alive", lambda p: True)

    stop_server(port=9500, lock_dir=tmp_path, timeout=0.05, _kill_fn=mock_kill)

    sigs = [sig for _, sig in kill_calls if _ == pid]
    assert signal.SIGTERM in sigs
    assert signal.SIGKILL in sigs


def test_stop_server_never_signals_self(tmp_path, monkeypatch):
    if sys.platform == "win32":
        pytest.skip("POSIX-only test")

    from biome_mcp import server_control
    from biome_mcp.server_control import stop_server

    self_pid = os.getpid()
    _make_lockfile(tmp_path, 9500, self_pid)

    kill_calls = []
    monkeypatch.setattr(server_control, "is_pid_alive", lambda p: True)

    result = stop_server(port=9500, lock_dir=tmp_path,
                         _kill_fn=lambda p, s: kill_calls.append((p, s)))

    assert kill_calls == []
    assert result is False


def test_stop_server_never_signals_parent(tmp_path, monkeypatch):
    if sys.platform == "win32":
        pytest.skip("POSIX-only test")

    from biome_mcp import server_control
    from biome_mcp.server_control import stop_server

    parent_pid = os.getppid()
    _make_lockfile(tmp_path, 9500, parent_pid)

    kill_calls = []
    monkeypatch.setattr(server_control, "is_pid_alive", lambda p: True)

    result = stop_server(port=9500, lock_dir=tmp_path,
                         _kill_fn=lambda p, s: kill_calls.append((p, s)))

    assert kill_calls == []
    assert result is False


def test_stop_server_windows_uses_taskkill(tmp_path, monkeypatch):
    from biome_mcp import server_control
    from biome_mcp.server_control import stop_server

    pid = 54321
    _make_lockfile(tmp_path, 9500, pid)

    run_calls = []

    def mock_run(cmd, **kwargs):
        run_calls.append(cmd)
        if "/F" not in cmd:
            for f in tmp_path.glob(f"server-9500-{pid}.lock"):
                f.unlink()

    def mock_alive(p):
        return (tmp_path / f"server-9500-{p}.lock").exists()

    monkeypatch.setattr(server_control, "is_pid_alive", mock_alive)
    monkeypatch.setattr(server_control, "_IS_WIN", True)

    result = stop_server(port=9500, lock_dir=tmp_path, _kill_fn=mock_run)

    assert any("/PID" in " ".join(cmd) and str(pid) in cmd for cmd in run_calls)
    assert result is True


def test_stop_server_windows_force_fallback(tmp_path, monkeypatch):
    from biome_mcp import server_control
    from biome_mcp.server_control import stop_server

    pid = 54321
    _make_lockfile(tmp_path, 9500, pid)

    run_calls = []

    def mock_run(cmd, **kwargs):
        run_calls.append(list(cmd))

    monkeypatch.setattr(server_control, "is_pid_alive", lambda p: True)
    monkeypatch.setattr(server_control, "_IS_WIN", True)

    stop_server(port=9500, lock_dir=tmp_path, timeout=0.05, _kill_fn=mock_run)

    cmds_flat = [" ".join(c) for c in run_calls]
    assert any("/F" in c for c in cmds_flat), f"Expected /F in: {cmds_flat}"


def test_stop_server_scoped_to_port(tmp_path, monkeypatch):
    if sys.platform == "win32":
        pytest.skip("POSIX-only test")

    from biome_mcp import server_control
    from biome_mcp.server_control import stop_server

    _make_lockfile(tmp_path, 9515, 111)
    _make_lockfile(tmp_path, 9602, 222)

    kill_calls = []

    def mock_kill(p, sig):
        kill_calls.append((p, sig))
        for f in tmp_path.glob(f"server-9515-{p}.lock"):
            f.unlink()

    monkeypatch.setattr(server_control, "is_pid_alive",
                        lambda p: (tmp_path / f"server-9515-{p}.lock").exists()
                        or (tmp_path / f"server-9602-{p}.lock").exists())

    stop_server(port=9515, lock_dir=tmp_path, _kill_fn=mock_kill)

    killed_pids = [p for p, _ in kill_calls]
    assert 111 in killed_pids
    assert 222 not in killed_pids


def test_stop_server_noop_on_stale_lockfile_dead_process(tmp_path, monkeypatch):
    from biome_mcp import server_control
    from biome_mcp.server_control import stop_server

    _make_lockfile(tmp_path, 9500, 99999)
    monkeypatch.setattr(server_control, "is_pid_alive", lambda p: False)

    kill_calls = []
    result = stop_server(port=9500, lock_dir=tmp_path,
                         _kill_fn=lambda p, s: kill_calls.append((p, s)))

    assert kill_calls == []
    assert result is False


# ── evict_duplicate_servers ───────────────────────────────────────────────────

@pytest.mark.skipif(sys.platform == "win32", reason="POSIX real-kill test")
def test_evict_kills_same_ppid_process(tmp_path):
    """Process whose lockfile ppid == our ppid is signaled and dies."""
    from biome_mcp.server_control import evict_duplicate_servers
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        _make_lockfile_with_meta(tmp_path, 9500, proc.pid, {"ppid": os.getppid()})
        count = evict_duplicate_servers(lock_dir=tmp_path)
        assert count == 1
        deadline = time.monotonic() + 6.0
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        assert proc.poll() is not None, "Duplicate process should have been killed"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_evict_leaves_different_ppid_alive(tmp_path, monkeypatch):
    """Process whose lockfile ppid is alive but != our ppid is NOT killed."""
    from biome_mcp import server_control
    from biome_mcp.server_control import evict_duplicate_servers

    stop_calls = []
    monkeypatch.setattr(server_control, "_send_stop", lambda *a: stop_calls.append(a[0]))

    fake_pid = 55555
    alive_ppid = os.getpid()
    _make_lockfile_with_meta(tmp_path, 9500, fake_pid, {"ppid": alive_ppid})
    monkeypatch.setattr(server_control, "is_pid_alive",
                        lambda p: p in {fake_pid, alive_ppid})

    count = evict_duplicate_servers(lock_dir=tmp_path)
    assert count == 0
    assert fake_pid not in stop_calls


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX real-kill test")
def test_evict_kills_orphaned_process(tmp_path):
    """Process whose lockfile ppid is dead is treated as orphan and killed."""
    from biome_mcp.server_control import evict_duplicate_servers
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        _make_lockfile_with_meta(tmp_path, 9500, proc.pid, {"ppid": 99999})
        count = evict_duplicate_servers(lock_dir=tmp_path)
        assert count == 1
        deadline = time.monotonic() + 6.0
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        assert proc.poll() is not None, "Orphaned process should have been killed"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_evict_skips_self_and_parent(tmp_path, monkeypatch):
    """evict_duplicate_servers never signals self or parent, even with matching ppid."""
    from biome_mcp import server_control
    from biome_mcp.server_control import evict_duplicate_servers

    stop_calls = []
    monkeypatch.setattr(server_control, "_send_stop", lambda *a: stop_calls.append(a[0]))
    monkeypatch.setattr(server_control, "is_pid_alive", lambda p: True)

    _make_lockfile_with_meta(tmp_path, 9500, os.getpid(), {"ppid": os.getppid()})
    _make_lockfile_with_meta(tmp_path, 9500, os.getppid(), {"ppid": os.getppid()})

    count = evict_duplicate_servers(lock_dir=tmp_path)
    assert count == 0
    assert stop_calls == []


def test_evict_no_metadata_skips_gracefully(tmp_path, monkeypatch):
    """Lock file with no JSON on line 2 is skipped without error."""
    from biome_mcp import server_control
    from biome_mcp.server_control import evict_duplicate_servers

    stop_calls = []
    monkeypatch.setattr(server_control, "_send_stop", lambda *a: stop_calls.append(a[0]))

    fake_pid = 55556
    monkeypatch.setattr(server_control, "is_pid_alive", lambda p: p == fake_pid)
    (tmp_path / f"server-9500-{fake_pid}.lock").write_text(f"{fake_pid}\n", encoding="utf-8")

    count = evict_duplicate_servers(lock_dir=tmp_path)
    assert count == 0
    assert stop_calls == []


def test_evict_returns_count(tmp_path, monkeypatch):
    """Return value equals the number of processes successfully signaled."""
    from biome_mcp import server_control
    from biome_mcp.server_control import evict_duplicate_servers

    stop_calls = []
    monkeypatch.setattr(server_control, "_send_stop", lambda *a: stop_calls.append(a[0]))

    parent_pid = os.getppid()
    pids = [55557, 55558]
    for pid in pids:
        _make_lockfile_with_meta(tmp_path, 9500, pid, {"ppid": parent_pid})
    monkeypatch.setattr(server_control, "is_pid_alive", lambda p: p in pids)

    count = evict_duplicate_servers(lock_dir=tmp_path)
    assert count == 2
    assert set(stop_calls) == set(pids)


# ── is_pid_alive / _read_ppid_from_lock_path (self-contained, no engine deps) ──

def test_is_pid_alive_true_for_self():
    from biome_mcp.server_control import is_pid_alive
    assert is_pid_alive(os.getpid()) is True


def test_is_pid_alive_false_for_none():
    from biome_mcp.server_control import is_pid_alive
    assert is_pid_alive(None) is False


def test_read_ppid_from_lock_path_returns_none_when_missing(tmp_path):
    from biome_mcp.server_control import _read_ppid_from_lock_path
    f = _make_lockfile(tmp_path, 9500, 123)
    assert _read_ppid_from_lock_path(f) is None


def test_read_ppid_from_lock_path_reads_metadata(tmp_path):
    from biome_mcp.server_control import _read_ppid_from_lock_path
    f = _make_lockfile_with_meta(tmp_path, 9500, 123, {"ppid": 999})
    assert _read_ppid_from_lock_path(f) == 999
