"""Interactive REPL shell for BiomeCLI — stdlib readline only."""
from __future__ import annotations

import shlex
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from biome_mcp.cli.app import BiomeCLI


class ShellCompleter:
    """Tab-complete subcommands and tool names."""

    def __init__(self, cli: BiomeCLI) -> None:
        self._cli = cli
        self._matches: list[str] = []

    def _candidates(self) -> list[str]:
        names = list(self._cli.registry.keys())
        names.extend(t["name"] for t in self._cli.provider.list_tools())
        return sorted(set(names))

    def complete(self, text: str, state: int) -> str | None:
        if state == 0:
            candidates = self._candidates()
            self._matches = [c for c in candidates if c.startswith(text)]
        return self._matches[state] if state < len(self._matches) else None


def run_shell(cli: BiomeCLI) -> int:
    """Run interactive REPL. Returns 0 on clean exit."""
    import readline

    completer = ShellCompleter(cli)
    readline.set_completer(completer.complete)
    if getattr(readline, "backend", "") == "editline":
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    prompt = f"{cli._name}> "
    print("Interactive shell. Type 'help' for commands, Ctrl-D to exit.")

    while True:
        try:
            line = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in ("exit", "quit"):
            break
        try:
            argv = shlex.split(line)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            continue
        cli.dispatch_one(argv)

    return 0
