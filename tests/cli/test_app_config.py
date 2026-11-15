"""S5-S7: AppConfig load/save."""
from __future__ import annotations

import json
from pathlib import Path

from biome_mcp.cli.app_config import AppConfig


def test_s5_load_missing_file(tmp_path: Path) -> None:
    cfg = AppConfig.load(tmp_path / "no-such-file.json")
    assert cfg.host == "localhost"
    assert cfg.port == 0


def test_s6_load_corrupt_json(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{broken", encoding="utf-8")
    cfg = AppConfig.load(p)
    assert cfg.host == "localhost"
    assert cfg.port == 0


def test_s6_load_valid_json(tmp_path: Path) -> None:
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"host": "10.0.0.1", "port": 7000}), encoding="utf-8")
    cfg = AppConfig.load(p)
    assert cfg.host == "10.0.0.1"
    assert cfg.port == 7000


def test_s7_save_atomic(tmp_path: Path) -> None:
    p = tmp_path / "sub" / "config.json"
    cfg = AppConfig(host="10.0.0.1", port=7000)
    cfg.save(p)

    assert p.exists()
    assert not p.with_suffix(".tmp").exists()

    loaded = json.loads(p.read_text(encoding="utf-8"))
    assert loaded["host"] == "10.0.0.1"
    assert loaded["port"] == 7000


def test_s6_load_stringified_port(tmp_path: Path) -> None:
    p = tmp_path / "config.json"
    p.write_text(json.dumps({"host": 123, "port": "7000"}), encoding="utf-8")
    cfg = AppConfig.load(p)
    assert cfg.port == 7000
    assert isinstance(cfg.port, int)
    assert cfg.host == "123"


def test_s7_save_overwrites(tmp_path: Path) -> None:
    p = tmp_path / "config.json"
    AppConfig(port=100).save(p)
    AppConfig(port=200).save(p)
    loaded = json.loads(p.read_text(encoding="utf-8"))
    assert loaded["port"] == 200
