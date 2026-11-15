"""Tests for follow.py: parse_interval (F1-F6), follow_loop (F14-F21)."""
from __future__ import annotations

import asyncio
import io
import json

import pytest

from biome_mcp.cli.follow import follow_loop, parse_interval
from biome_mcp.cli.follow_policy import FollowPolicy, _default_is_done
from biome_mcp.models.result import CommandResult, CommandStatus


# --- parse_interval F1-F6 ---

def test_F1_seconds():
    assert parse_interval("10s") == 10.0

def test_F2_minutes():
    assert parse_interval("2m") == 120.0

def test_F3_zero_seconds():
    assert parse_interval("0s") == 0.0

def test_F4_bad_string():
    with pytest.raises(ValueError):
        parse_interval("bad")

def test_F5_empty():
    with pytest.raises(ValueError):
        parse_interval("")

def test_F6_no_unit():
    with pytest.raises(ValueError):
        parse_interval("5")


# --- is_done (_default_is_done) F7-F13 ---

def test_F7_done_status():
    assert _default_is_done(CommandResult.ok('{"status": "done"}'))

def test_F8_complete_status():
    assert _default_is_done(CommandResult.ok('{"status": "complete"}'))

def test_F9_finished_status():
    assert _default_is_done(CommandResult.ok('{"status": "finished"}'))

def test_F10_running_status():
    assert not _default_is_done(CommandResult.ok('{"status": "running"}'))

def test_F11_plain_text():
    assert not _default_is_done(CommandResult.ok("plain text, no json"))

def test_F12_empty_text():
    assert not _default_is_done(CommandResult.ok(""))

def test_F13_other_key():
    assert not _default_is_done(CommandResult.ok('{"other": "key"}'))


# --- follow_loop F14-F21 ---

def _queue(*responses: CommandResult):
    items = list(responses)
    async def call_async(name, args):
        return items.pop(0)
    return call_async

def _lines(buf: io.StringIO) -> list[dict]:
    return [json.loads(l) for l in buf.getvalue().strip().splitlines() if l.strip()]

def _schema_ok(line: dict) -> bool:
    return (
        isinstance(line.get("poll"), int) and line["poll"] >= 1
        and isinstance(line.get("ts"), float)
        and isinstance(line.get("status"), str)
        and isinstance(line.get("text"), str)
    )


async def test_F14_done_on_first_poll():
    buf = io.StringIO()
    code = await follow_loop(
        _queue(CommandResult.ok('{"status": "done"}')),
        "tool", {}, interval=0.0, out=buf,
    )
    lines = _lines(buf)
    assert code == 0
    assert len(lines) == 1
    assert lines[0].get("complete") is True
    assert _schema_ok(lines[0])


async def test_F15_three_running_then_done():
    buf = io.StringIO()
    code = await follow_loop(
        _queue(
            CommandResult.ok("running"),
            CommandResult.ok("running"),
            CommandResult.ok("running"),
            CommandResult.ok('{"status": "done"}'),
        ),
        "tool", {}, interval=0.0, out=buf,
    )
    lines = _lines(buf)
    assert code == 0
    assert len(lines) == 4
    assert lines[-1].get("complete") is True
    assert all(not l.get("complete") for l in lines[:-1])
    assert all(_schema_ok(l) for l in lines)


async def test_F16_max_polls():
    buf = io.StringIO()
    code = await follow_loop(
        _queue(CommandResult.ok("running"), CommandResult.ok("running")),
        "tool", {}, interval=0.0, max_polls=2, out=buf,
    )
    lines = _lines(buf)
    assert code == 0
    assert len(lines) == 2
    assert lines[-1].get("complete") is True


async def test_F17_failed_result():
    buf = io.StringIO()
    code = await follow_loop(
        _queue(CommandResult.error("E_FAIL", "boom")),
        "tool", {}, interval=0.0, out=buf,
    )
    lines = _lines(buf)
    assert code == 1
    assert len(lines) == 1
    assert lines[0].get("error") is True
    assert _schema_ok(lines[0])


async def test_F18_keyboard_interrupt():
    count = 0

    async def _ki_on_second(name, args):
        nonlocal count
        count += 1
        if count == 2:
            raise KeyboardInterrupt
        return CommandResult.ok("running")

    buf = io.StringIO()
    code = await follow_loop(_ki_on_second, "tool", {}, interval=0.0, out=buf)
    lines = _lines(buf)
    assert code == 130
    assert lines[-1].get("interrupted") is True


async def test_F18b_cancelled_error():
    count = 0

    async def _cancel_on_second(name, args):
        nonlocal count
        count += 1
        if count == 2:
            raise asyncio.CancelledError
        return CommandResult.ok("running")

    buf = io.StringIO()
    code = await follow_loop(_cancel_on_second, "tool", {}, interval=0.0, out=buf)
    lines = _lines(buf)
    assert code == 130
    assert lines[-1].get("interrupted") is True


async def test_F19_non_json_then_done():
    buf = io.StringIO()
    code = await follow_loop(
        _queue(
            CommandResult.ok("still running"),
            CommandResult.ok("still running"),
            CommandResult.ok('{"status": "done"}'),
        ),
        "tool", {}, interval=0.0, out=buf,
    )
    lines = _lines(buf)
    assert code == 0
    assert len(lines) == 3
    assert all(_schema_ok(l) for l in lines)


async def test_F20_empty_then_done():
    buf = io.StringIO()
    code = await follow_loop(
        _queue(CommandResult.ok(""), CommandResult.ok('{"status": "done"}')),
        "tool", {}, interval=0.0, out=buf,
    )
    lines = _lines(buf)
    assert code == 0
    assert len(lines) == 2


async def test_F21_max_polls_1000_done_on_1():
    buf = io.StringIO()
    code = await follow_loop(
        _queue(CommandResult.ok('{"status": "done"}')),
        "tool", {}, interval=0.0, max_polls=1000, out=buf,
    )
    lines = _lines(buf)
    assert code == 0
    assert len(lines) == 1
    assert lines[0].get("complete") is True
