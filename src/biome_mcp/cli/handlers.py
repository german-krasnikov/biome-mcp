"""Built-in CLI subcommand handlers — engine-agnostic."""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING

from biome_mcp.errors import BiomeError, ErrorCode

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

        print(f"Usage: {app_name} <command|tool> [args]\n")
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
        p.add_argument("--dry-run", action="store_true", dest="dry_run")
        known, rest = p.parse_known_args(argv)

        if known.follow is not None:
            from .follow_handler import run_follow
            return run_follow(provider, rest, known.follow, known.max_polls, spec, follow)

        if not rest:
            _err("error: call requires a tool name")
            return 3
        name, *kv = rest

        from .formatters import generate_example, suggest_tool, validate_required
        from .generic import exit_code_for, parse_kv

        info = provider.get_tool(name)
        if info is None:
            hint = suggest_tool(name, provider)
            if hint:
                _err(f"error: tool '{name}' not found. Did you mean: {hint}")
            else:
                _err(f"error: tool '{name}' not found")
            return exit_code_for(BiomeError(ErrorCode.COMMAND_NOT_FOUND, name))

        try:
            args = parse_kv(kv)
        except ValueError as exc:
            _err(f"error: {exc}")
            return 3

        missing = validate_required(info, args)
        if missing:
            example = generate_example(info)
            _err(f"error: missing required: {', '.join(missing)}")
            if example:
                _err(f"  example: {example}")
            return 3

        if known.dry_run:
            print(f"[dry-run] {name} {args}")
            return 0

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


def make_batch_handler(provider: ToolProvider) -> _Handler:
    from .batch_handler import make_batch_handler as _make
    return _make(provider)
