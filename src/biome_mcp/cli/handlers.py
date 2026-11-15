"""Built-in CLI subcommand handlers — engine-agnostic."""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from biome_mcp.errors import BiomeError

from ._constants import BUILTIN_DESCS, BUILTIN_USAGE, TOOL_HINT_THRESHOLD
from .formatters import (
    matches_effect,
    matches_grep,
    matches_ns,
    print_flat,
    print_grouped,
    render_tool_info,
)

if TYPE_CHECKING:
    from biome_mcp.cli.app import ToolProvider
    from biome_mcp.cli.connection import ConnectionSpec
    from biome_mcp.cli.follow_policy import FollowPolicy
    from biome_mcp.schema_registry import SchemaRegistry

_Handler = Callable[[list[str]], int]


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def make_help_handler(app_name: str, registry: dict[str, object]) -> _Handler:
    def handler(argv: list[str]) -> int:
        if argv:
            sub = argv[0]
            if sub in BUILTIN_USAGE:
                print(f"Usage: {app_name} {BUILTIN_USAGE[sub]}")
            elif sub in registry:
                print(f"Usage: {app_name} {sub} [args]")
            else:
                _err(f"error: unknown subcommand '{sub}'")
                return 1
            return 0

        print(f"Usage: {app_name} <command> [args]\n")
        print("Commands:")
        for name, desc in BUILTIN_DESCS.items():
            print(f"  {name:<10} {desc}")
        custom = [k for k in registry if k not in BUILTIN_DESCS]
        if custom:
            print("\nApp commands:")
            for name in custom:
                print(f"  {name}")
        return 0

    return handler


def make_list_handler(provider: ToolProvider) -> _Handler:
    def handler(argv: list[str]) -> int:
        p = argparse.ArgumentParser(prog="list", add_help=False)
        p.add_argument("--ns", default=None)
        p.add_argument("--effect", default=None)
        p.add_argument("--grep", default=None)
        p.add_argument("--json", action="store_true", dest="as_json")
        p.add_argument("--flat", action="store_true")
        args = p.parse_args(argv)

        tools = provider.list_tools()
        visible = [
            t for t in tools
            if matches_ns(t, args.ns)
            and matches_effect(t, args.effect)
            and matches_grep(t, args.grep)
        ]

        if args.as_json:
            data = [
                {k: v for k, v in t.items() if k != "input_schema"}
                for t in visible
            ]
            print(json.dumps(data))
            return 0

        use_flat = args.flat or args.ns or args.effect or args.grep
        if use_flat or not visible:
            print_flat(visible)
        else:
            print_grouped(visible)

        if len(visible) > TOOL_HINT_THRESHOLD:
            print(
                f"\nShows {len(visible)} tools."
                f" Use --ns, --effect, --grep to narrow."
            )
        return 0

    return handler


def make_describe_handler(
    provider: ToolProvider,
    registry: SchemaRegistry | None = None,
    app_name: str = "biome",
) -> _Handler:
    def handler(argv: list[str]) -> int:
        p = argparse.ArgumentParser(prog="describe", add_help=False)
        p.add_argument("tool", nargs="?", default=None)
        p.add_argument("--json", action="store_true", dest="as_json")
        args = p.parse_args(argv)

        if not args.tool:
            _err("error: describe requires tool name")
            return 3

        info = provider.get_tool(args.tool)
        if info is None:
            _err(f"error: tool '{args.tool}' not found")
            _err(f"hint: run `{app_name} list` to see available tools")
            return 2

        if args.as_json:
            print(json.dumps(dict(info)))
            return 0

        if registry is not None and registry.get_full(args.tool):
            print(registry.format_text([args.tool]))
        else:
            print(render_tool_info(info))
        return 0

    return handler


def make_call_handler(
    provider: ToolProvider,
    spec: ConnectionSpec | None = None,
    follow: FollowPolicy | None = None,
) -> _Handler:
    def handler(argv: list[str]) -> int:
        if not argv:
            _err("error: call requires a tool name")
            return 3

        p = argparse.ArgumentParser(add_help=False)
        p.add_argument("--follow", default=None)
        p.add_argument("--max-polls", type=int, default=None, dest="max_polls")
        known, rest = p.parse_known_args(argv)

        if known.follow is not None:
            return _run_follow(provider, rest, known.follow, known.max_polls, spec, follow)

        if not rest:
            _err("error: call requires a tool name")
            return 3
        name, *kv = rest

        from .generic import exit_code_for, parse_kv

        try:
            args = parse_kv(kv)
        except ValueError as exc:
            _err(f"error: {exc}")
            return 3
        try:
            result = provider.call_tool_sync(name, args)
        except BiomeError as exc:
            _err(f"error: {name}: {exc.message}")
            return exit_code_for(exc)
        print(result.text)
        if not result.complete:
            print("[truncated — use compress=true or reduce scope]")
        return 0

    return handler


def _run_follow(
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
    from .generic import parse_kv

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
                    provider.call_tool_async, name, args, interval, max_polls, policy
                )

        return asyncio.run(_with_session())

    return asyncio.run(
        follow_loop(provider.call_tool_async, name, args, interval, max_polls, policy)
    )


def make_batch_handler(provider: ToolProvider) -> _Handler:
    def handler(argv: list[str]) -> int:
        from biome_mcp.batch.parser import parse_batch

        from .generic import exit_code_for

        p = argparse.ArgumentParser(prog="batch", add_help=False)
        p.add_argument("dsl", nargs="?", default="")
        p.add_argument("--file", default=None)
        args = p.parse_args(argv)

        dsl = args.dsl
        if args.file:
            try:
                dsl = Path(args.file).read_text(encoding="utf-8")
            except OSError as exc:
                _err(f"error: {exc}")
                return 1

        try:
            doc = parse_batch(dsl)
        except BiomeError as exc:
            _err(f"error: batch: {exc.message}")
            return exit_code_for(exc)

        any_error = False
        multi = len(doc.commands) > 1
        for cmd in doc.commands:
            cmd_args = {a.key: a.value for a in cmd.args}
            try:
                result = provider.call_tool_sync(cmd.name, cmd_args)
                prefix = f"{cmd.name}: " if multi else ""
                print(f"{prefix}{result.text}")
            except BiomeError as exc:
                _err(f"error: batch[{cmd.ordinal}]: {cmd.name}: {exc.message}")
                any_error = True

        return 1 if any_error else 0

    return handler
