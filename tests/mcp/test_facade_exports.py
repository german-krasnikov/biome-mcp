"""biome_mcp.mcp facade re-exports the SDK's ToolError and Context for callers
that should not import `mcp.server.mcpserver.*` paths directly."""

from __future__ import annotations


def test_tool_error_reexported():
    from mcp.server.mcpserver.exceptions import ToolError as SdkToolError

    from biome_mcp.mcp import ToolError

    assert ToolError is SdkToolError


def test_context_reexported():
    from mcp.server.mcpserver import Context as SdkContext

    from biome_mcp.mcp import Context

    assert Context is SdkContext
