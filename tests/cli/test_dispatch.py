"""S8-S9 help, S27-S31 dispatch and custom subcommands, S32+ implicit call."""
from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout, suppress

from biome_mcp.cli.app import BiomeCLI
from biome_mcp.models.result import CommandResult
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


def test_s29_unknown_command_stderr_nonzero() -> None:
    """S29: unknown command (not a tool) → error on stderr, non-zero exit."""
    out, err, code = run_cmd(["unknowncmd"])
    assert code != 0
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


def test_s32_implicit_tool_call() -> None:
    """S32: 'animator action=get' without 'call' → routes to call handler."""
    results = {"animator": CommandResult.ok("state=idle")}
    out, err, code = run_cmd(["animator", "action=get", "path=/Player"], results=results)
    assert code == 0
    assert "state=idle" in out


def test_s33_implicit_call_output_passthrough() -> None:
    """S33: implicit call prints result.text as-is."""
    results = {"scene_inspect": CommandResult.ok("42 objects")}
    out, err, code = run_cmd(["scene_inspect", "depth=5"], results=results)
    assert code == 0
    assert "42 objects" in out


def test_s34_explicit_call_still_works() -> None:
    """S34: backward compat — 'call animator action=get path=/P' still works."""
    results = {"animator": CommandResult.ok("ok")}
    out, err, code = run_cmd(["call", "animator", "action=get", "path=/P"], results=results)
    assert code == 0
    assert "ok" in out


def test_s35_subcommand_wins_over_tool() -> None:
    """S35: registered subcommand always wins over tool name."""
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
