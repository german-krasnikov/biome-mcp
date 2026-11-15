"""AppProfile validation tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_mcp.cli.app_profile import AppProfile


def test_frozen() -> None:
    p = AppProfile(app_name="test", data_dir=Path("/tmp"))
    with pytest.raises(AttributeError):
        p.app_name = "changed"  # type: ignore[misc]


def test_defaults() -> None:
    p = AppProfile(app_name="test")
    assert p.protocol == "tcp"
    assert p.default_port == 0
    assert p.default_host == "localhost"


def test_empty_name_raises() -> None:
    with pytest.raises(ValueError, match="app_name"):
        AppProfile(app_name="")


def test_relative_data_dir_raises() -> None:
    with pytest.raises(ValueError, match="data_dir"):
        AppProfile(app_name="test", data_dir=Path("relative/path"))
