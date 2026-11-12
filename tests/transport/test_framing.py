"""TCP framing: 4-byte big-endian length prefix + payload, and socket options."""

from __future__ import annotations

import asyncio
import socket
import struct
import sys
from unittest.mock import AsyncMock, Mock

import pytest

from biome_mcp.transport.framing import (
    MAX_FRAME_BYTES,
    _apply_socket_options,
    frame_read,
    frame_read_with_timeout,
    frame_write,
)


def _make_writer():
    writer = Mock()
    writer.write = Mock()
    return writer


def _make_reader(*chunks):
    r = AsyncMock()
    r.readexactly = AsyncMock(side_effect=list(chunks))
    return r


# ── frame_write ───────────────────────────────────────────────────────────────

def test_frame_write_produces_correct_wire_format():
    payload = b'{"id":"0001","cmd":"ping","args":{}}'
    writer = _make_writer()
    frame_write(writer, payload)
    written = writer.write.call_args[0][0]
    assert written[:4] == struct.pack("!I", len(payload))
    assert written[4:] == payload
    assert len(written) == 4 + len(payload)


def test_frame_write_empty_payload():
    writer = _make_writer()
    frame_write(writer, b"")
    written = writer.write.call_args[0][0]
    assert written == b"\x00\x00\x00\x00"


# ── frame_read ────────────────────────────────────────────────────────────────

async def test_frame_read_normal():
    payload = b'{"id":"0001","ok":true}'
    hdr = struct.pack("!I", len(payload))
    reader = _make_reader(hdr, payload)
    result = await frame_read(reader)
    assert result == payload
    assert reader.readexactly.call_count == 2


async def test_frame_read_rejects_zero_length():
    reader = asyncio.StreamReader()
    reader.feed_data(struct.pack("!I", 0))
    reader.feed_eof()
    with pytest.raises(ConnectionError, match="Frame size"):
        await frame_read(reader)


async def test_frame_read_rejects_oversized():
    reader = asyncio.StreamReader()
    reader.feed_data(struct.pack("!I", MAX_FRAME_BYTES + 1))
    reader.feed_eof()
    with pytest.raises(ConnectionError, match="Frame size"):
        await frame_read(reader)


async def test_frame_read_accepts_small():
    reader = asyncio.StreamReader()
    reader.feed_data(struct.pack("!I", 5) + b"hello")
    reader.feed_eof()
    assert await frame_read(reader) == b"hello"


async def test_frame_read_header_incomplete_raises():
    reader = _make_reader(asyncio.IncompleteReadError(b"\x00", 4))
    with pytest.raises(asyncio.IncompleteReadError):
        await frame_read(reader)


async def test_frame_read_write_roundtrip():
    original = b'{"id":"0001","cmd":"get_hierarchy"}'
    buf = bytearray()

    class _FakeWriter:
        def write(self, data: bytes) -> None:
            buf.extend(data)

    frame_write(_FakeWriter(), original)
    reader = asyncio.StreamReader()
    reader.feed_data(bytes(buf))
    reader.feed_eof()
    assert await frame_read(reader) == original


# ── frame_read_with_timeout ────────────────────────────────────────────────────

async def test_frame_read_with_timeout_rejects_oversized():
    reader = asyncio.StreamReader()
    reader.feed_data(struct.pack("!I", MAX_FRAME_BYTES + 1))
    reader.feed_eof()
    with pytest.raises(ConnectionError, match="Frame size"):
        await frame_read_with_timeout(reader, timeout=1.0)


async def test_frame_read_with_timeout_fires_on_hung_read():
    reader = asyncio.StreamReader()  # never fed -> readexactly hangs
    with pytest.raises(TimeoutError):
        await frame_read_with_timeout(reader, timeout=0.05)


# ── _apply_socket_options ──────────────────────────────────────────────────────

def _tcp_pair():
    """A connected (client, server) pair of real AF_INET/SOCK_STREAM sockets
    (socket.socketpair() yields AF_UNIX on macOS, which rejects TCP_* opts)."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(listener.getsockname())
    server, _ = listener.accept()
    listener.close()
    return client, server


def test_apply_socket_options_safe_with_none():
    _apply_socket_options(None)  # must not raise


def test_apply_socket_options_sets_nodelay_and_keepalive():
    a, b = _tcp_pair()
    try:
        _apply_socket_options(a)
        assert a.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY) != 0
        assert a.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE) != 0
    finally:
        a.close()
        b.close()


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-specific keepalive opts")
def test_apply_socket_options_darwin_keepalive_values():
    a, b = _tcp_pair()
    try:
        _apply_socket_options(a)
        assert a.getsockopt(socket.IPPROTO_TCP, 0x10) == 60
        assert a.getsockopt(socket.IPPROTO_TCP, 0x101) == 10
    finally:
        a.close()
        b.close()
