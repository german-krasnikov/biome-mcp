"""S1-S3: ToolProvider Protocol and ToolInfo contract."""
from __future__ import annotations

from biome_mcp.cli.app import ToolInfo
from tests.cli.conftest import FAKE_TOOLS, FakeToolProvider


def test_s1_fake_provider_satisfies_protocol() -> None:
    """S1: FakeProvider duck-types ToolProvider (has all required methods)."""
    p = FakeToolProvider()
    assert callable(p.list_tools)
    assert callable(p.get_tool)
    assert callable(p.call_tool_sync)
    tools = p.list_tools()
    assert isinstance(tools, list)


def test_s2_tool_info_has_required_fields() -> None:
    """S2: ToolInfo with required + optional fields."""
    t = FAKE_TOOLS[0]  # scene_inspect
    assert t["name"] == "scene_inspect"
    assert "description" in t
    assert "input_schema" in t
    assert t["effect"] == "read"
    assert t["namespace"] == "scene"


def test_s2_tool_info_minimal_valid() -> None:
    """S2: ToolInfo with only required fields (optional fields absent)."""
    t: ToolInfo = {"name": "ping", "description": "pong", "input_schema": {}}
    assert t["name"] == "ping"
    assert "effect" not in t
    assert "namespace" not in t


def test_s3_get_tool_known() -> None:
    """S3: get_tool returns ToolInfo for known name."""
    p = FakeToolProvider()
    t = p.get_tool("animator")
    assert t is not None
    assert t["name"] == "animator"


def test_s3_get_tool_unknown() -> None:
    """S3: get_tool returns None for unknown name."""
    p = FakeToolProvider()
    assert p.get_tool("nonexistent") is None
