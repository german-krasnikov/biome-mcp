"""CompactMCP: schema hooks, strict args, and helper functions."""

from __future__ import annotations

import pytest

from biome_mcp.mcp.compose import (
    CompactMCP,
    apply_schema_hooks,
    forbid_extra_properties,
    inject_descriptions,
    inject_extras,
    strip_titles,
)
from mcp.server.mcpserver.exceptions import ToolError


def test_strip_titles():
    schema = {"title": "Root", "properties": {"a": {"title": "A", "type": "string"}}}
    strip_titles("t", schema)
    assert "title" not in schema
    assert "title" not in schema["properties"]["a"]


def test_forbid_extra_properties():
    schema = {"properties": {"a": {"type": "string"}}}
    forbid_extra_properties("t", schema)
    assert schema["additionalProperties"] is False


def test_forbid_extra_properties_no_overwrite():
    schema = {"properties": {"a": {}}, "additionalProperties": True}
    forbid_extra_properties("t", schema)
    assert schema["additionalProperties"] is True


def test_forbid_extra_properties_no_props():
    schema: dict = {}
    forbid_extra_properties("t", schema)
    assert "additionalProperties" not in schema


def test_inject_descriptions():
    hook = inject_descriptions(
        by_tool={"tool1": {"path": "The object path"}},
        common={"timeout": "Max seconds"},
    )
    schema = {"properties": {"path": {}, "timeout": {}, "other": {}}}
    hook("tool1", schema)
    assert schema["properties"]["path"]["description"] == "The object path"
    assert schema["properties"]["timeout"]["description"] == "Max seconds"
    assert "description" not in schema["properties"]["other"]


def test_inject_descriptions_no_overwrite():
    hook = inject_descriptions(by_tool={"t": {"a": "new"}})
    schema = {"properties": {"a": {"description": "existing"}}}
    hook("t", schema)
    assert schema["properties"]["a"]["description"] == "existing"


def test_inject_extras():
    hook = inject_extras(by_tool={"t": {"path": {"pattern": "^/.*"}}})
    schema = {"properties": {"path": {"type": "string"}}}
    hook("t", schema)
    assert schema["properties"]["path"]["pattern"] == "^/.*"


def test_inject_extras_no_overwrite():
    hook = inject_extras(by_tool={"t": {"a": {"pattern": "new"}}})
    schema = {"properties": {"a": {"pattern": "existing"}}}
    hook("t", schema)
    assert schema["properties"]["a"]["pattern"] == "existing"


@pytest.mark.anyio
async def test_compact_mcp_add_tool_applies_hooks():
    hooks_called: list[tuple[str, dict]] = []

    def spy_hook(name: str, schema: dict) -> None:
        hooks_called.append((name, dict(schema)))

    server = CompactMCP("test", schema_hooks=[forbid_extra_properties, spy_hook])

    def my_tool(x: str) -> str:
        return x

    server.add_tool(my_tool)
    assert len(hooks_called) == 1
    assert hooks_called[0][0] == "my_tool"
    tool = server._tool_manager._tools["my_tool"]
    assert tool.parameters.get("additionalProperties") is False


@pytest.mark.anyio
async def test_compact_mcp_structured_output_always_false():
    server = CompactMCP("test")

    def my_tool(x: str) -> str:
        return x

    server.add_tool(my_tool, structured_output=True)
    tool = server._tool_manager._tools["my_tool"]
    assert tool.output_schema is None


@pytest.mark.anyio
async def test_compact_mcp_reject_unknown_args():
    server = CompactMCP("test", schema_hooks=[forbid_extra_properties], reject_unknown_args=True)

    def my_tool(x: str) -> str:
        return x

    server.add_tool(my_tool)
    with pytest.raises(ToolError, match="unknown argument.*bogus"):
        await server.call_tool("my_tool", {"x": "ok", "bogus": "bad"})


@pytest.mark.anyio
async def test_compact_mcp_no_reject_by_default():
    server = CompactMCP("test", schema_hooks=[forbid_extra_properties])

    def my_tool(x: str) -> str:
        return x

    server.add_tool(my_tool)
    result = await server.call_tool("my_tool", {"x": "ok", "bogus": "ignored"})
    assert result is not None


def test_apply_schema_hooks():
    from mcp.server.mcpserver import MCPServer

    server = MCPServer("test")

    def my_tool(a: str) -> str:
        return a

    server.add_tool(my_tool)
    apply_schema_hooks(server, [forbid_extra_properties, strip_titles])
    tool = server._tool_manager._tools["my_tool"]
    assert tool.parameters.get("additionalProperties") is False
    assert "title" not in tool.parameters


def test_auto_title():
    server = CompactMCP("test")

    def find_objects(query: str) -> str:
        return query

    server.add_tool(find_objects)
    tool = server._tool_manager._tools["find_objects"]
    assert tool.title == "Find Objects"
