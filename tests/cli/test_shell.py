"""Tests for REPL shell mode."""
from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from biome_mcp.cli.app import BiomeCLI
from biome_mcp.cli.shell import ShellCompleter
from biome_mcp.models.result import CommandResult
from tests.cli.conftest import FakeToolProvider


def test_shell_completer_includes_tools_and_subcommands() -> None:
    provider = FakeToolProvider()
    cli = BiomeCLI(provider, name="test-app")
    completer = ShellCompleter(cli)
    candidates = completer._candidates()
    assert "list" in candidates
    assert "describe" in candidates
    assert "scene_inspect" in candidates
    assert "animator" in candidates


def test_shell_completer_prefix_match() -> None:
    provider = FakeToolProvider()
    cli = BiomeCLI(provider, name="test-app")
    completer = ShellCompleter(cli)
    assert completer.complete("scene", 0) is not None
    assert "scene" in completer.complete("scene", 0)


def test_shell_completer_no_match() -> None:
    provider = FakeToolProvider()
    cli = BiomeCLI(provider, name="test-app")
    completer = ShellCompleter(cli)
    assert completer.complete("zzzzz", 0) is None


def test_shell_exit_on_quit() -> None:
    provider = FakeToolProvider()
    cli = BiomeCLI(provider, name="test-app")
    with patch("builtins.input", side_effect=["quit"]):
        from biome_mcp.cli.shell import run_shell
        out = io.StringIO()
        with redirect_stdout(out):
            code = run_shell(cli)
    assert code == 0


def test_shell_exit_on_eof() -> None:
    provider = FakeToolProvider()
    cli = BiomeCLI(provider, name="test-app")
    with patch("builtins.input", side_effect=EOFError):
        from biome_mcp.cli.shell import run_shell
        out = io.StringIO()
        with redirect_stdout(out):
            code = run_shell(cli)
    assert code == 0


def test_shell_runs_command() -> None:
    results = {"scene_inspect": CommandResult.ok("42 objects")}
    provider = FakeToolProvider(results=results)
    cli = BiomeCLI(provider, name="test-app")
    with patch("builtins.input", side_effect=["scene_inspect", "exit"]):
        from biome_mcp.cli.shell import run_shell
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = run_shell(cli)
    assert code == 0
    assert "42 objects" in out.getvalue()


def test_shell_subcommand_registered() -> None:
    provider = FakeToolProvider()
    cli = BiomeCLI(provider, name="test-app")
    assert "shell" in cli._registry
