"""S8-S9 help, S27-S31 dispatch and custom subcommands."""
from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout, suppress

from biome_mcp.cli.app import BiomeCLI
from tests.cli.conftest import FakeToolProvider, run_cmd


def test_s8_help_lists_builtins() -> None:
    """S8: dispatch(["help"]) prints built-in subcommand names."""
    out, err, code = run_cmd(["help"])
    assert code == 0
    assert "list" in out
    assert "describe" in out
    assert "call" in out
    assert "batch" in out


def test_s9_help_per_subcommand() -> None:
    """S9: dispatch(["help", "call"]) prints call usage."""
    out, err, code = run_cmd(["help", "call"])
    assert code == 0
    assert "call" in out.lower()


def test_s27_dispatch_empty_calls_serve() -> None:
    """S27: empty argv → calls serve() when provided."""
    called: list[bool] = []

    def serve() -> None:
        called.append(True)

    run_cmd([], serve=serve)
    assert called == [True]


def test_s27_dispatch_empty_no_serve_shows_help() -> None:
    """S27: empty argv without serve → shows help, exit 0."""
    out, err, code = run_cmd([])
    assert code == 0
    assert len(out.strip()) > 0  # something printed


def test_s28_serve_subcommand() -> None:
    """S28: dispatch(["serve"]) → calls serve()."""
    called: list[bool] = []

    def serve() -> None:
        called.append(True)

    run_cmd(["serve"], serve=serve)
    assert called == [True]


def test_s29_unknown_command_stderr_exit1() -> None:
    """S29: unknown command → error on stderr, exit 1."""
    out, err, code = run_cmd(["unknowncmd"])
    assert code == 1
    assert "unknowncmd" in err


def test_s30_custom_subcommand() -> None:
    """S30: cli.add("custom", fn) → fn called with remaining argv."""
    called: list[list[str]] = []

    def my_cmd(argv: list[str]) -> int:
        called.append(argv)
        return 0

    provider = FakeToolProvider()
    cli = BiomeCLI(provider, name="test-app")
    cli.add("custom", my_cmd)

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err), suppress(SystemExit):
        cli.dispatch(["custom", "a", "b"])

    assert called == [["a", "b"]]


def test_s31_override_builtin() -> None:
    """S31: add("list", fn) → consumer fn wins over built-in."""
    called: list[bool] = []

    def my_list(argv: list[str]) -> int:
        called.append(True)
        return 0

    provider = FakeToolProvider()
    cli = BiomeCLI(provider, name="test-app")
    cli.add("list", my_list)

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err), suppress(SystemExit):
        cli.dispatch(["list"])

    assert called == [True]
