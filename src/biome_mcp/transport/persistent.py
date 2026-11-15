"""Persistent asyncio TCP session for --follow mode polling."""
from __future__ import annotations

import asyncio
from contextvars import ContextVar

from biome_mcp.transport.framing import apply_socket_options, frame_read_with_timeout, frame_write

_session_var: ContextVar[TcpSession | None] = ContextVar("tcp_session", default=None)

DEFAULT_TIMEOUT = 15.0


class TcpSession:
    """Async context manager that owns one persistent (reader, writer) pair.

    Sets _session_var on enter, resets on exit.
    Reconnects once on ConnectionError/EOFError; raises on second failure.
    """

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._token = None

    async def __aenter__(self) -> "TcpSession":
        await self._connect()
        self._token = _session_var.set(self)
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._token is not None:
            _session_var.reset(self._token)
        await self._close()

    async def _connect(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
        sock = self._writer.transport.get_extra_info("socket")
        if sock is not None:
            apply_socket_options(sock)

    async def _close(self) -> None:
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None

    async def call(self, payload: bytes, *, timeout: float = DEFAULT_TIMEOUT) -> bytes:
        """frame_write + frame_read over the persistent stream. Reconnects once."""
        try:
            return await self._do_call(payload, timeout)
        except (ConnectionError, EOFError, asyncio.IncompleteReadError):
            await self._close()
            await self._connect()
            return await self._do_call(payload, timeout)

    async def _do_call(self, payload: bytes, timeout: float) -> bytes:
        assert self._reader is not None and self._writer is not None
        frame_write(self._writer, payload)
        await self._writer.drain()
        return await frame_read_with_timeout(self._reader, timeout)


def get_active_session() -> "TcpSession | None":
    """Return the session set by the enclosing TcpSession context, or None."""
    return _session_var.get()
