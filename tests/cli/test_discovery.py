"""S15: discover_instances merges lockfiles + port files, dedupes by port."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from biome_mcp.cli.app_profile import AppProfile
from biome_mcp.cli.discovery import discover_instances
from biome_mcp.cli.ports import write_port_file


def _profile(tmp_path: Path) -> AppProfile:
    return AppProfile(
        app_name="test-app",
        protocol="tcp",
        default_port=6400,
        default_host="localhost",
        data_dir=tmp_path,
    )


def test_s15_merge_lockfiles_and_port_files(tmp_path: Path) -> None:
    profile = _profile(tmp_path)

    lock_dir = tmp_path / "locks"
    lock_dir.mkdir()
    (lock_dir / "server-6400-111.lock").write_text("111", encoding="utf-8")

    write_port_file(6401, 222, profile)

    with (
        patch("biome_mcp.cli.discovery.is_pid_alive", return_value=True),
        patch(
            "biome_mcp.cli.discovery.list_servers",
            return_value=[
                {"port": 6400, "pid": 111, "lock_path": lock_dir / "server-6400-111.lock"},
            ],
        ),
    ):
        result = discover_instances(profile)

    assert len(result) == 2
    assert result[0].port == 6400
    assert result[0].source == "lock"
    assert result[1].port == 6401
    assert result[1].source == "port_file"


def test_s15_dedup_by_port(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    write_port_file(6400, 333, profile)

    with (
        patch("biome_mcp.cli.discovery.is_pid_alive", return_value=True),
        patch(
            "biome_mcp.cli.discovery.list_servers",
            return_value=[{"port": 6400, "pid": 111, "lock_path": Path("x")}],
        ),
    ):
        result = discover_instances(profile)

    assert len(result) == 1
    assert result[0].source == "lock"


def test_s15_stale_port_file_filtered(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    write_port_file(6400, 99999, profile)

    with (
        patch("biome_mcp.cli.discovery.is_pid_alive", return_value=False),
        patch("biome_mcp.cli.discovery.list_servers", return_value=[]),
    ):
        result = discover_instances(profile)

    assert len(result) == 0


def test_s15_pid_none_port_file_included(tmp_path: Path) -> None:
    """Port file with unreadable PID is included (conservative: can't prove dead)."""
    profile = _profile(tmp_path)
    d = tmp_path / "ports"
    d.mkdir()
    (d / "6402.port").write_text("garbage", encoding="utf-8")

    with (
        patch("biome_mcp.cli.discovery.is_pid_alive", return_value=False),
        patch("biome_mcp.cli.discovery.list_servers", return_value=[]),
    ):
        result = discover_instances(profile)

    assert len(result) == 1
    assert result[0].port == 6402
    assert result[0].source == "port_file"
    assert result[0].label is None


def test_s15_empty(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    with patch("biome_mcp.cli.discovery.list_servers", return_value=[]):
        result = discover_instances(profile)
    assert result == []
