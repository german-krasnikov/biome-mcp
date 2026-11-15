"""S8-S12: ConnectionResolver priority chain."""
from __future__ import annotations

import json
from pathlib import Path

from biome_mcp.cli.app_profile import AppProfile
from biome_mcp.cli.ports import write_port_file
from biome_mcp.cli.resolver import ConnectionResolver


def _profile(tmp_path: Path) -> AppProfile:
    return AppProfile(
        app_name="test-app",
        protocol="tcp",
        default_port=6400,
        default_host="localhost",
        data_dir=tmp_path,
    )


def test_s8_cli_flag_highest_priority(tmp_path: Path) -> None:
    r = ConnectionResolver(_profile(tmp_path))
    spec = r.resolve(cli_port=6401)
    assert spec.port == 6401
    assert spec.source == "flag"
    assert spec.host == "localhost"


def test_s8_cli_flag_with_host(tmp_path: Path) -> None:
    r = ConnectionResolver(_profile(tmp_path))
    spec = r.resolve(cli_port=6401, cli_host="10.0.0.1")
    assert spec.host == "10.0.0.1"
    assert spec.source == "flag"


def test_s9_env_var(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setenv("BIOME_TEST_APP_PORT", "7000")  # type: ignore[attr-defined]
    r = ConnectionResolver(_profile(tmp_path))
    spec = r.resolve()
    assert spec.port == 7000
    assert spec.source == "env"


def test_s9_env_var_with_host(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setenv("BIOME_TEST_APP_PORT", "7000")  # type: ignore[attr-defined]
    monkeypatch.setenv("BIOME_TEST_APP_HOST", "10.0.0.2")  # type: ignore[attr-defined]
    r = ConnectionResolver(_profile(tmp_path))
    spec = r.resolve()
    assert spec.host == "10.0.0.2"


def test_s10_config_file(tmp_path: Path) -> None:
    cfg_path = tmp_path / "cli-config.json"
    cfg_path.write_text(json.dumps({"host": "10.0.0.3", "port": 8000}), encoding="utf-8")
    r = ConnectionResolver(_profile(tmp_path))
    spec = r.resolve()
    assert spec.port == 8000
    assert spec.host == "10.0.0.3"
    assert spec.source == "config"


def test_s11_port_file(tmp_path: Path, monkeypatch: object) -> None:
    profile = _profile(tmp_path)
    write_port_file(9000, 99999, profile)
    monkeypatch.setattr(  # type: ignore[attr-defined]
        "biome_mcp.cli.resolver.is_pid_alive", lambda pid: True,
    )
    r = ConnectionResolver(profile)
    spec = r.resolve()
    assert spec.port == 9000
    assert spec.source == "port_file"


def test_s11_port_file_stale_skipped(tmp_path: Path, monkeypatch: object) -> None:
    profile = _profile(tmp_path)
    write_port_file(9000, 99999, profile)
    monkeypatch.setattr(  # type: ignore[attr-defined]
        "biome_mcp.cli.resolver.is_pid_alive", lambda pid: False,
    )
    r = ConnectionResolver(profile)
    spec = r.resolve()
    assert spec.source == "default"


def test_s12_default_fallback(tmp_path: Path) -> None:
    r = ConnectionResolver(_profile(tmp_path))
    spec = r.resolve()
    assert spec.port == 6400
    assert spec.host == "localhost"
    assert spec.source == "default"
    assert spec.protocol == "tcp"
    assert spec.app_name == "test-app"


def test_s11_lockfile_fallback(tmp_path: Path, monkeypatch: object) -> None:
    """Lockfile-only server (no port file) is found by resolve()."""
    profile = _profile(tmp_path)
    lock_dir = tmp_path / "locks"
    lock_dir.mkdir()
    (lock_dir / "server-6500-111.lock").write_text("111", encoding="utf-8")

    monkeypatch.setattr(  # type: ignore[attr-defined]
        "biome_mcp.cli.resolver.is_pid_alive", lambda pid: True,
    )
    monkeypatch.setattr(  # type: ignore[attr-defined]
        "biome_mcp.cli.resolver.list_servers",
        lambda d: [{"port": 6500, "pid": 111, "lock_path": lock_dir / "server-6500-111.lock"}],
    )
    r = ConnectionResolver(profile)
    spec = r.resolve()
    assert spec.port == 6500
    assert spec.source == "lock"


def test_s8_flag_beats_env(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setenv("BIOME_TEST_APP_PORT", "7000")  # type: ignore[attr-defined]
    r = ConnectionResolver(_profile(tmp_path))
    spec = r.resolve(cli_port=6401)
    assert spec.source == "flag"
    assert spec.port == 6401
