"""S2-S4: env var resolution."""
from __future__ import annotations

from biome_mcp.cli.env_vars import env_host, env_key, env_port


def test_s2_env_key_format() -> None:
    assert env_key("unity-biome-mcp", "PORT") == "BIOME_UNITY_BIOME_MCP_PORT"
    assert env_key("unity-biome-mcp", "HOST") == "BIOME_UNITY_BIOME_MCP_HOST"


def test_s2_env_key_simple_name() -> None:
    assert env_key("browser-mcp", "PORT") == "BIOME_BROWSER_MCP_PORT"


def test_s3_env_port_set(monkeypatch: object) -> None:
    monkeypatch.setenv("BIOME_UNITY_BIOME_MCP_PORT", "6401")  # type: ignore[attr-defined]
    assert env_port("unity-biome-mcp") == 6401


def test_s3_env_port_invalid(monkeypatch: object) -> None:
    monkeypatch.setenv("BIOME_UNITY_BIOME_MCP_PORT", "not_a_number")  # type: ignore[attr-defined]
    assert env_port("unity-biome-mcp") is None


def test_s4_env_port_absent() -> None:
    assert env_port("nonexistent-app-xyz") is None


def test_s4_env_host_absent() -> None:
    assert env_host("nonexistent-app-xyz") is None


def test_s3_env_host_set(monkeypatch: object) -> None:
    monkeypatch.setenv("BIOME_UNITY_BIOME_MCP_HOST", "192.168.1.10")  # type: ignore[attr-defined]
    assert env_host("unity-biome-mcp") == "192.168.1.10"
