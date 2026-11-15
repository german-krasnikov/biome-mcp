"""Tests for FollowPolicy extension points (G1-G7)."""
from __future__ import annotations

import asyncio
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from biome_mcp.cli.app import BiomeCLI
from biome_mcp.cli.follow import follow_loop
from biome_mcp.cli.follow_policy import FollowPolicy
from biome_mcp.errors import BiomeError, ErrorCode
from biome_mcp.models.result import CommandResult


class FakeToolProvider:
    def __init__(self):
        pass

    def list_tools(self) -> list:
        return []

    def get_tool(self, name: str):
        return None

    def call_tool_sync(self, name: str, args: dict) -> CommandResult:
        raise BiomeError(ErrorCode.COMMAND_NOT_FOUND, f"tool '{name}' not found")


class FakeAsyncProvider(FakeToolProvider):
    def __init__(self, responses=None):
        super().__init__()
        self._responses = list(responses or [CommandResult.ok('{"status": "done"}')])

    async def call_tool_async(self, name: str, args: dict[str, Any]) -> CommandResult:
        if self._responses:
            return self._responses.pop(0)
        return CommandResult.ok('{"status": "done"}')


def _lines(buf: io.StringIO) -> list[dict]:
    return [json.loads(l) for l in buf.getvalue().strip().splitlines() if l.strip()]


async def test_G1_custom_is_done():
    policy = FollowPolicy(is_done=lambda r: "DONE" in r.text)
    buf = io.StringIO()
    # "DONE" text matches custom is_done; {"status":"done"} alone would NOT match
    code = await follow_loop(
        FakeAsyncProvider([CommandResult.ok("DONE")]).call_tool_async,
        "tool", {}, interval=0.0, policy=policy, out=buf,
    )
    lines = _lines(buf)
    assert code == 0
    assert lines[0].get("complete") is True


async def test_G2_custom_format_line():
    fmt = lambda poll, result, final: f"[{poll}] {result.text}"
    policy = FollowPolicy(format_line=fmt)
    buf = io.StringIO()
    code = await follow_loop(
        FakeAsyncProvider([CommandResult.ok("progress data")]).call_tool_async,
        "tool", {}, interval=0.0, max_polls=1, policy=policy, out=buf,
    )
    output = buf.getvalue().strip()
    assert code == 0
    assert output.startswith("[1] progress data")


async def test_G3_max_retries_suppresses_then_fails():
    policy = FollowPolicy(max_retries=2)
    responses = [
        CommandResult.error("E", "fail 1"),
        CommandResult.error("E", "fail 2"),
        CommandResult.error("E", "fail 3"),
    ]
    buf = io.StringIO()
    code = await follow_loop(
        FakeAsyncProvider(responses).call_tool_async,
        "tool", {}, interval=0.0, policy=policy, out=buf,
    )
    lines = _lines(buf)
    assert code == 1
    assert len(lines) == 3
    assert all(l.get("error") is True for l in lines)
    assert lines[0].get("retry") == 1
    assert lines[1].get("retry") == 2
    assert "retry" not in lines[2]  # fatal — no retry key


async def test_G3_max_retries_reset_on_success():
    policy = FollowPolicy(max_retries=1)
    responses = [
        CommandResult.error("E", "fail"),
        CommandResult.ok("ok"),              # success resets counter
        CommandResult.error("E", "fail"),
        CommandResult.error("E", "fatal"),   # 2nd consecutive error (> max_retries=1)
    ]
    buf = io.StringIO()
    code = await follow_loop(
        FakeAsyncProvider(responses).call_tool_async,
        "tool", {}, interval=0.0, policy=policy, out=buf,
    )
    assert code == 1
    lines = _lines(buf)
    assert len(lines) == 4


async def test_G4_interval_bounds_clamp():
    policy = FollowPolicy(interval_bounds=(1.0, 60.0))
    sleep_calls: list[float] = []

    async def _fake_sleep(secs):
        sleep_calls.append(secs)

    provider = FakeAsyncProvider([CommandResult.ok("running"), CommandResult.ok('{"status": "done"}')])
    with patch("asyncio.sleep", side_effect=_fake_sleep):
        buf = io.StringIO()
        code = await follow_loop(
            provider.call_tool_async, "tool", {}, interval=0.0, policy=policy, out=buf,
        )
    assert code == 0
    # interval was 0.0, clamped to 1.0
    assert sleep_calls == [1.0]


async def test_G5_poll_timeout():
    policy = FollowPolicy(poll_timeout=0.001)  # max_retries=0 by default

    async def slow_call(name, args):
        await asyncio.sleep(10.0)
        return CommandResult.ok("done")

    buf = io.StringIO()
    code = await follow_loop(slow_call, "tool", {}, interval=0.0, policy=policy, out=buf)
    assert code == 1
    lines = _lines(buf)
    assert len(lines) == 1
    assert lines[0].get("error") is True
    assert lines[0]["status"] == "timed_out"


def _dispatch(cli: BiomeCLI, argv: list[str]) -> tuple[str, str, int]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            cli.dispatch(argv)
        except SystemExit as e:
            return out.getvalue(), err.getvalue(), int(e.code or 0)
    return out.getvalue(), err.getvalue(), 0


def test_G6_default_policy_available():
    provider = FakeAsyncProvider()
    cli = BiomeCLI(provider)  # no follow= arg
    out, err, code = _dispatch(cli, ["call", "--follow", "0s", "scene_inspect"])
    assert code == 0
    lines = _lines(io.StringIO(out))
    assert lines[0].get("complete") is True


def test_G7_explicit_policy_same_as_default():
    p1 = FakeAsyncProvider()
    p2 = FakeAsyncProvider()
    cli1 = BiomeCLI(p1)
    cli2 = BiomeCLI(p2, follow=FollowPolicy())

    out1, _, code1 = _dispatch(cli1, ["call", "--follow", "0s", "scene_inspect"])
    out2, _, code2 = _dispatch(cli2, ["call", "--follow", "0s", "scene_inspect"])

    assert code1 == code2 == 0
    l1 = _lines(io.StringIO(out1))
    l2 = _lines(io.StringIO(out2))
    assert l1[0].get("complete") == l2[0].get("complete") is True
