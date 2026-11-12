"""MCP SDK integration layer — the only subpackage that may import `mcp`."""

from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

__all__ = ["Context", "ToolError"]
