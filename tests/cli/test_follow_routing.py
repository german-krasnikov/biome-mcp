"""Tests for --follow routing in handlers.py (F22-F26)."""
from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from typing import Any

import pytest

from biome_mcp.cli.app import ToolInfo
from biome_mcp.cli.handlers import make_call_handler
from biome_mcp.errors import BiomeError, ErrorCode
from biome_mcp.models.result import CommandResult


class FakeToolProvider:
    def __init__(self, results=None):
        self._results = results or {}

    def list_tools(self) -> list:
        return []

    def get_tool(self, name: str):
        if name in self._results:
            return {"name": name, "description": "", "input_schema": {}}
        return None

    def call_tool_sync(self, name: str, args: dict) -> CommandResult:
        if name not in self._results:
            raise BiomeError(ErrorCode.COMMAND_NOT_FOUND, f"tool '{name}' not found")
        return self._results[name]


class FakeAsyncProvider(FakeToolProvider):
    """FakeToolProvider with call_tool_async for --follow tests."""

    async def call_tool_async(self, name: str, args: dict[str, Any]) -> CommandResult:
        return CommandResult.ok('{"status": "done"}')


def _run(handler, argv: list[str]) -> tuple[str, str, int]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = handler(argv)
    return out.getvalue(), err.getvalue(), code


def test_F22_no_async_support():
    provider = FakeToolProvider()  # no call_tool_async
    handler = make_call_handler(provider)
    out, err, code = _run(handler, ["--follow", "1s", "scene_inspect"])
    assert code == 1
    assert "does not support" in err


def test_F23_bad_interval():
    provider = FakeAsyncProvider()
    handler = make_call_handler(provider)
    out, err, code = _run(handler, ["--follow", "bad-interval", "scene_inspect"])
    assert code == 3
    assert "--follow" in err


def test_F24_no_tool_name():
    provider = FakeAsyncProvider()
    handler = make_call_handler(provider)
    out, err, code = _run(handler, ["--follow", "1s"])
    assert code == 3
    assert "tool name" in err


def test_F25_no_follow_regression():
    provider = FakeToolProvider(results={"scene_inspect": CommandResult.ok("ok result")})
    handler = make_call_handler(provider)
    out, err, code = _run(handler, ["scene_inspect"])
    assert code == 0
    assert "ok result" in out


def test_F26_working_follow():
    provider = FakeAsyncProvider()
    handler = make_call_handler(provider)
    out, err, code = _run(handler, ["--follow", "0s", "scene_inspect"])
    assert code == 0
    lines = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
    assert len(lines) == 1
    assert lines[0].get("complete") is True
