"""Tests for TcpSession: context var, reconnect (T1-T6)."""
from __future__ import annotations

import struct
from unittest.mock import AsyncMock, Mock, patch

import pytest

from biome_mcp.transport.persistent import TcpSession, get_active_session


def _make_writer() -> Mock:
    w = Mock()
    w.write = Mock()
    w.drain = AsyncMock()
    w.close = Mock()
    w.wait_closed = AsyncMock()
    w.transport = Mock()
    w.transport.get_extra_info = Mock(return_value=None)
    return w


def _make_reader(response: bytes) -> AsyncMock:
    header = struct.pack(">I", len(response))
    r = AsyncMock()
    r.readexactly = AsyncMock(side_effect=[header, response])
    return r


def _make_fail_reader() -> AsyncMock:
    r = AsyncMock()
    r.readexactly = AsyncMock(side_effect=ConnectionResetError("fail"))
    return r


async def test_T1_contextvar_set():
    reader = _make_reader(b"ok")
    writer = _make_writer()
    with patch("asyncio.open_connection", AsyncMock(return_value=(reader, writer))):
        async with TcpSession("localhost", 9600) as session:
            assert get_active_session() is session


async def test_T2_contextvar_reset():
    reader = _make_reader(b"ok")
    writer = _make_writer()
    with patch("asyncio.open_connection", AsyncMock(return_value=(reader, writer))):
        async with TcpSession("localhost", 9600):
            pass
    assert get_active_session() is None


async def test_T3_call_success():
    response = b"hello world"
    reader = _make_reader(response)
    writer = _make_writer()
    with patch("asyncio.open_connection", AsyncMock(return_value=(reader, writer))):
        async with TcpSession("localhost", 9600) as session:
            result = await session.call(b"ping")
    assert result == response


async def test_T4_reconnect_once():
    response = b"after reconnect"
    fail_reader = _make_fail_reader()
    fail_writer = _make_writer()
    ok_reader = _make_reader(response)
    ok_writer = _make_writer()

    open_conn = AsyncMock(side_effect=[
        (fail_reader, fail_writer),
        (ok_reader, ok_writer),
    ])
    with patch("asyncio.open_connection", open_conn):
        async with TcpSession("localhost", 9600) as session:
            result = await session.call(b"ping")

    assert result == response
    assert open_conn.call_count == 2


async def test_T5_double_failure():
    fail_reader_1 = _make_fail_reader()
    fail_reader_2 = _make_fail_reader()
    fail_writer_1 = _make_writer()
    fail_writer_2 = _make_writer()

    open_conn = AsyncMock(side_effect=[
        (fail_reader_1, fail_writer_1),
        (fail_reader_2, fail_writer_2),
    ])
    with patch("asyncio.open_connection", open_conn):
        async with TcpSession("localhost", 9600) as session:
            with pytest.raises(ConnectionError):
                await session.call(b"ping")


async def test_T6_nested_sessions():
    r1, w1 = _make_reader(b"r1"), _make_writer()
    r2, w2 = _make_reader(b"r2"), _make_writer()

    with patch("asyncio.open_connection", AsyncMock(side_effect=[(r1, w1), (r2, w2)])):
        async with TcpSession("h1", 1) as outer:
            assert get_active_session() is outer
            async with TcpSession("h2", 2) as inner:
                assert get_active_session() is inner
            assert get_active_session() is outer
    assert get_active_session() is None
