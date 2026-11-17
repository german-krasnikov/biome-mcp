"""Follow-mode handler — extracted from handlers.py for P22."""
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from biome_mcp.cli.app import ToolProvider
    from biome_mcp.cli.connection import ConnectionSpec
    from biome_mcp.cli.follow_policy import FollowPolicy


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def run_follow(
    provider: ToolProvider,
    argv: list[str],
    follow_str: str,
    max_polls: int | None,
    spec: ConnectionSpec | None,
    follow: FollowPolicy | None,
) -> int:
    import asyncio

    from biome_mcp.cli.follow import follow_loop, parse_interval
    from biome_mcp.cli.follow_policy import FollowPolicy as _FP

    try:
        interval = parse_interval(follow_str)
    except ValueError as exc:
        _err(f"error: --follow: {exc}")
        return 3

    if not argv:
        _err("error: call requires a tool name")
        return 3

    name, *rest = argv
    from biome_mcp.cli.generic import parse_kv

    try:
        args = parse_kv(rest)
    except ValueError as exc:
        _err(f"error: {exc}")
        return 3

    if not hasattr(provider, "call_tool_async"):
        _err("error: provider does not support --follow")
        return 1

    policy = follow if follow is not None else _FP()

    if spec is not None and spec.protocol == "tcp":
        from biome_mcp.transport.persistent import TcpSession

        async def _with_session() -> int:
            async with TcpSession(spec.host, spec.port):
                return await follow_loop(
                    provider.call_tool_async, name, args,
                    interval, max_polls, policy,
                )

        return asyncio.run(_with_session())

    return asyncio.run(
        follow_loop(
            provider.call_tool_async, name, args,
            interval, max_polls, policy,
        )
    )
