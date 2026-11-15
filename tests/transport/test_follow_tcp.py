"""Integration tests: handlers TCP routing + TcpSession (T7-T9)."""
from __future__ import annotations

import asyncio
import struct
from unittest.mock import AsyncMock, Mock

import pytest

from biome_mcp.cli.connection import ConnectionSpec
from biome_mcp.cli.follow import follow_loop
from biome_mcp.cli.follow_policy import FollowPolicy
from biome_mcp.models.result import CommandResult
from biome_mcp.transport.persistent import TcpSession, get_active_session


def _make_stream_pair(response: bytes = b'{"status":"done"}'):
    header = struct.pack(">I", len(response))
    reader = AsyncMock()
    reader.readexactly = AsyncMock(side_effect=[header, response])
    writer = Mock()
    writer.write = Mock()
    writer.drain = AsyncMock()
    writer.close = Mock()
    writer.wait_closed = AsyncMock()
    writer.transport = Mock()
    writer.transport.get_extra_info = Mock(return_value=None)
    return reader, writer


async def test_T7_contextvar_set_during_follow(monkeypatch):
    """_run_follow with spec.protocol='tcp' sets ContextVar during follow_loop."""
    reader, writer = _make_stream_pair()
    monkeypatch.setattr(
        "biome_mcp.transport.persistent.asyncio.open_connection",
        AsyncMock(return_value=(reader, writer)),
    )

    captured_sessions = []

    async def _capturing_call(name, args):
        captured_sessions.append(get_active_session())
        return CommandResult.ok('{"status": "done"}')

    spec = ConnectionSpec(host="127.0.0.1", port=9600, protocol="tcp", app_name="test", source="flag")
    async with TcpSession(spec.host, spec.port):
        code = await follow_loop(_capturing_call, "tool", {}, interval=0.0, policy=FollowPolicy())

    assert code == 0
    assert len(captured_sessions) == 1
    assert captured_sessions[0] is not None
    assert get_active_session() is None


async def test_T8_no_tcp_without_spec(monkeypatch):
    """Without spec, asyncio.open_connection is never called."""
    open_mock = AsyncMock()
    monkeypatch.setattr(
        "biome_mcp.transport.persistent.asyncio.open_connection", open_mock
    )

    async def _done(name, args):
        return CommandResult.ok('{"status": "done"}')

    code = await follow_loop(_done, "tool", {}, interval=0.0, policy=FollowPolicy())
    assert code == 0
    open_mock.assert_not_called()


async def test_T9_session_identity_stable_across_polls(monkeypatch):
    """get_active_session() returns the same instance across two polls."""
    response = b'{"status":"running"}'
    header = struct.pack(">I", len(response))
    done_response = b'{"status":"done"}'
    done_header = struct.pack(">I", len(done_response))

    reader = AsyncMock()
    reader.readexactly = AsyncMock(side_effect=[
        header, response, header, response, done_header, done_response,
    ])
    writer = Mock()
    writer.write = Mock()
    writer.drain = AsyncMock()
    writer.close = Mock()
    writer.wait_closed = AsyncMock()
    writer.transport = Mock()
    writer.transport.get_extra_info = Mock(return_value=None)

    monkeypatch.setattr(
        "biome_mcp.transport.persistent.asyncio.open_connection",
        AsyncMock(return_value=(reader, writer)),
    )

    captured_sessions = []

    async def _capture_and_respond(name, args):
        captured_sessions.append(get_active_session())
        if len(captured_sessions) >= 2:
            return CommandResult.ok('{"status": "done"}')
        return CommandResult.ok("running")

    async with TcpSession("127.0.0.1", 9600):
        code = await follow_loop(
            _capture_and_respond, "tool", {}, interval=0.0, policy=FollowPolicy()
        )

    assert code == 0
    assert len(captured_sessions) == 2
    assert captured_sessions[0] is captured_sessions[1]
