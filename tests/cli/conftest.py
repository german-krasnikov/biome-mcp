"""Shared fixtures for CLI tests."""
from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from typing import Any

from biome_mcp.cli.app import BiomeCLI, ToolInfo
from biome_mcp.errors import BiomeError, ErrorCode
from biome_mcp.models.result import CommandResult

FAKE_TOOLS: list[ToolInfo] = [
    {
        "name": "scene_inspect",
        "description": "Inspect scene hierarchy",
        "input_schema": {"properties": {"depth": {"type": "integer"}}, "required": []},
        "effect": "read",
        "namespace": "scene",
    },
    {
        "name": "scene_diff",
        "description": "Compare scene states",
        "input_schema": {},
        "effect": "read",
        "namespace": "scene",
    },
    {
        "name": "animator",
        "description": "Animator Controller — state machine",
        "input_schema": {
            "properties": {
                "action": {"type": "string"},
                "path": {"type": "string"},
            },
            "required": ["action", "path"],
        },
        "effect": "write",
        "namespace": "animator",
    },
    {
        "name": "get_hierarchy",
        "description": "Get object hierarchy",
        "input_schema": {"properties": {"depth": {"type": "integer"}}, "required": []},
        "effect": "read",
        "namespace": "get",
    },
    {
        "name": "collider_mesh",
        "description": "Collider mesh inspector",
        "input_schema": {},
        "effect": "write",
        "namespace": "collider",
    },
]


class FakeToolProvider:
    def __init__(
        self,
        tools: list[ToolInfo] | None = None,
        results: dict[str, CommandResult] | None = None,
    ) -> None:
        self._tools = tools if tools is not None else FAKE_TOOLS
        self._results = results or {}

    def list_tools(self) -> list[ToolInfo]:
        return self._tools

    def get_tool(self, name: str) -> ToolInfo | None:
        return next((t for t in self._tools if t["name"] == name), None)

    def call_tool_sync(self, name: str, args: dict[str, Any]) -> CommandResult:
        if name not in self._results:
            raise BiomeError(ErrorCode.COMMAND_NOT_FOUND, f"tool '{name}' not found")
        return self._results[name]


def run_cmd(
    argv: list[str],
    tools: list[ToolInfo] | None = None,
    results: dict[str, CommandResult] | None = None,
    serve: Any = None,
) -> tuple[str, str, int]:
    """Run CLI dispatch, return (stdout, stderr, exit_code)."""
    provider = FakeToolProvider(tools, results)
    cli = BiomeCLI(provider, name="test-app", serve=serve)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            cli.dispatch(argv)
        except SystemExit as e:
            return out.getvalue(), err.getvalue(), int(e.code or 0)
    return out.getvalue(), err.getvalue(), 0
