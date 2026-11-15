"""S1: ConnectionSpec — frozen, hashable, slots."""
from __future__ import annotations

from biome_mcp.cli.connection import ConnectionSpec


def test_s1_frozen_hashable() -> None:
    spec = ConnectionSpec(
        host="localhost", port=6400, protocol="tcp",
        app_name="test-app", source="default",
    )
    assert hash(spec) == hash(spec)
    assert spec.port == 6400
    assert spec.source == "default"


def test_s1_slots() -> None:
    spec = ConnectionSpec(
        host="localhost", port=6400, protocol="tcp",
        app_name="test-app", source="flag",
    )
    assert hasattr(spec, "__slots__")


def test_s1_equality() -> None:
    a = ConnectionSpec("localhost", 6400, "tcp", "app", "flag")
    b = ConnectionSpec("localhost", 6400, "tcp", "app", "flag")
    assert a == b


def test_s1_label_optional() -> None:
    spec = ConnectionSpec("localhost", 6400, "tcp", "app", "flag")
    assert spec.label is None
    spec2 = ConnectionSpec("localhost", 6400, "tcp", "app", "flag", label="main")
    assert spec2.label == "main"
