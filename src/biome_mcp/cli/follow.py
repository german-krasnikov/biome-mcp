"""--follow polling loop for the CLI call subcommand."""
from __future__ import annotations

import asyncio
import json
import sys
import time
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, TextIO

from biome_mcp.models.result import CommandResult, CommandStatus

if TYPE_CHECKING:
    from biome_mcp.cli.follow_policy import FollowPolicy


def parse_interval(value: str) -> float:
    """Parse "10s" or "2m" → float seconds. Raises ValueError on bad input."""
    if not value:
        raise ValueError("interval must be like '10s' or '2m'")
    if value.endswith("s"):
        try:
            return float(value[:-1])
        except ValueError:
            pass
    elif value.endswith("m"):
        try:
            return float(value[:-1]) * 60.0
        except ValueError:
            pass
    raise ValueError(f"unrecognised interval {value!r}, expected e.g. '10s' or '2m'")


def _default_format_line(poll: int, result: CommandResult, is_final: bool) -> str:
    line: dict = {
        "poll": poll,
        "status": str(result.status),
        "text": result.text,
        "ts": time.time(),
    }
    if is_final:
        line["complete"] = True
    return json.dumps(line)


async def follow_loop(
    call_async: Callable[[str, dict], Awaitable[CommandResult]],
    name: str,
    args: dict,
    interval: float,
    max_polls: int | None = None,
    policy: FollowPolicy | None = None,
    out: TextIO | None = None,
) -> int:
    """Run polling loop. Returns exit code (0 / 1 / 130)."""
    from biome_mcp.cli.follow_policy import FollowPolicy as _FP

    if out is None:
        out = sys.stdout
    if policy is None:
        policy = _FP()

    # Clamp interval to policy bounds
    lo, hi = policy.interval_bounds
    interval = max(lo, min(hi, interval))

    poll = 0
    consecutive_errors = 0

    try:
        while True:
            poll += 1

            # Execute poll with optional timeout
            try:
                if policy.poll_timeout is not None:
                    result = await asyncio.wait_for(
                        call_async(name, args), timeout=policy.poll_timeout
                    )
                else:
                    result = await call_async(name, args)
            except asyncio.TimeoutError:
                result = CommandResult.timed_out("poll timed out")

            is_error = result.status in (CommandStatus.FAILED, CommandStatus.CANCELLED, CommandStatus.TIMED_OUT)

            if is_error:
                consecutive_errors += 1
                fatal = consecutive_errors > policy.max_retries
                fmt = policy.format_line
                if fmt is not None:
                    print(fmt(poll, result, False), file=out, flush=True)
                else:
                    line: dict = {
                        "poll": poll,
                        "status": str(result.status),
                        "text": result.text,
                        "ts": time.time(),
                        "error": True,
                    }
                    if not fatal:
                        line["retry"] = consecutive_errors
                    print(json.dumps(line), file=out, flush=True)
                if fatal:
                    return 1
                await asyncio.sleep(interval)
                continue

            consecutive_errors = 0
            done = policy.is_done(result) or (max_polls is not None and poll >= max_polls)
            fmt = policy.format_line
            line_str = fmt(poll, result, done) if fmt is not None else _default_format_line(poll, result, done)
            print(line_str, file=out, flush=True)
            if done:
                return 0
            await asyncio.sleep(interval)

    except (KeyboardInterrupt, asyncio.CancelledError):
        print(
            json.dumps({"poll": poll, "status": "interrupted", "text": "", "interrupted": True, "ts": time.time()}),
            file=out,
            flush=True,
        )
        return 130
