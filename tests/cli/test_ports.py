"""S13-S14: port file registry."""
from __future__ import annotations

from pathlib import Path

from biome_mcp.cli.app_profile import AppProfile
from biome_mcp.cli.ports import iter_port_files, remove_port_file, write_port_file


def _profile(tmp_path: Path) -> AppProfile:
    return AppProfile(app_name="test-app", data_dir=tmp_path)


def test_s13_write_port_file(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    p = write_port_file(6400, 12345, profile)
    assert p.exists()
    assert p.name == "6400.port"
    assert p.read_text(encoding="utf-8") == "12345"


def test_s13_remove_port_file(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    write_port_file(6400, 12345, profile)
    remove_port_file(6400, profile)
    assert not (tmp_path / "ports" / "6400.port").exists()


def test_s14_iter_port_files(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    write_port_file(6400, 100, profile)
    write_port_file(6401, 200, profile)

    result = list(iter_port_files(profile))
    assert result == [(6400, 100), (6401, 200)]


def test_s14_iter_empty(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    assert list(iter_port_files(profile)) == []


def test_s14_iter_bad_pid(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    d = tmp_path / "ports"
    d.mkdir()
    (d / "6400.port").write_text("not_a_pid", encoding="utf-8")
    result = list(iter_port_files(profile))
    assert result == [(6400, None)]


def test_s14_iter_ignores_non_numeric_stem(tmp_path: Path) -> None:
    profile = _profile(tmp_path)
    d = tmp_path / "ports"
    d.mkdir()
    (d / "foo.port").write_text("123", encoding="utf-8")
    assert list(iter_port_files(profile)) == []
