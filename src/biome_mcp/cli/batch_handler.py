"""Batch handler — extracted from handlers.py for P22."""
from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from biome_mcp.errors import BiomeError

if TYPE_CHECKING:
    from biome_mcp.cli.app import ToolProvider

_Handler = Callable[[list[str]], int]


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def make_batch_handler(provider: ToolProvider) -> _Handler:
    def handler(argv: list[str]) -> int:
        from biome_mcp.batch.parser import parse_batch
        from biome_mcp.cli.generic import exit_code_for

        p = argparse.ArgumentParser(prog="batch", add_help=False)
        p.add_argument("dsl", nargs="?", default="")
        p.add_argument("--file", default=None)
        p.add_argument("--stdin", action="store_true")
        args = p.parse_args(argv)

        dsl = args.dsl
        if args.stdin:
            dsl = sys.stdin.read()
        elif args.file:
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
                _err(
                    f"error: batch[{cmd.ordinal}]: "
                    f"{cmd.name}: {exc.message}"
                )
                any_error = True

        return 1 if any_error else 0

    return handler
