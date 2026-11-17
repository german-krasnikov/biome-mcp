"""S22-S26: call, batch handlers and exit codes."""
from __future__ import annotations

import io
from unittest.mock import patch

from biome_mcp.cli.generic import exit_code_for
from biome_mcp.errors import BiomeError, ErrorCode
from biome_mcp.models.result import CommandResult, CommandStatus
from tests.cli.conftest import run_cmd

# --- Call S22-S23 ---


def test_s22_call_passes_kv_to_provider() -> None:
    """S22: call subcommand parses kv and calls provider."""
    results = {"animator": CommandResult.ok("done")}
    out, err, code = run_cmd(
        ["call", "animator", "action=get", "path=/Player"], results=results
    )
    assert code == 0


def test_s23_call_output_passthrough() -> None:
    """S23: result.text printed as-is."""
    results = {"animator": CommandResult.ok("raw output here")}
    out, err, code = run_cmd(
        ["call", "animator", "action=get", "path=/Player"], results=results,
    )
    assert code == 0
    assert "raw output here" in out


def test_s23_call_truncation_note() -> None:
    """S23: append truncation note when result.complete is False."""
    result = CommandResult(status=CommandStatus.OK, text="partial text", complete=False)
    out, err, code = run_cmd(
        ["call", "animator", "action=get", "path=/Player"],
        results={"animator": result},
    )
    assert "truncated" in out.lower()


def test_s22_call_unknown_tool_nonzero() -> None:
    """S22: unknown tool → non-zero exit."""
    out, err, code = run_cmd(["call", "unknown_tool"])
    assert code != 0


# --- Batch S24-S25 ---


def test_s24_batch_two_commands_ok() -> None:
    """S24: batch two commands, both OK → exit 0 with prefixed output."""
    results = {
        "scene_inspect": CommandResult.ok("42 objects"),
        "animator": CommandResult.ok("state added"),
    }
    dsl = "scene_inspect\nanimator"
    out, err, code = run_cmd(["batch", dsl], results=results)
    assert code == 0
    assert "scene_inspect" in out
    assert "animator" in out


def test_s25_batch_unknown_tool_nonzero() -> None:
    """S25: batch with unknown tool → non-zero exit."""
    out, err, code = run_cmd(["batch", "totally_unknown_tool"])
    assert code != 0


def test_batch_stdin() -> None:
    """batch --stdin reads DSL from stdin."""
    results = {"scene_inspect": CommandResult.ok("42")}
    with patch("sys.stdin", io.StringIO("scene_inspect")):
        out, err, code = run_cmd(["batch", "--stdin"], results=results)
    assert code == 0
    assert "42" in out


# --- Exit codes S26 ---


def test_s26_exit_code_ok() -> None:
    assert exit_code_for(None) == 0


def test_s26_exit_code_command_not_found() -> None:
    assert exit_code_for(BiomeError(ErrorCode.COMMAND_NOT_FOUND, "")) == 2


def test_s26_exit_code_invalid_arguments() -> None:
    assert exit_code_for(BiomeError(ErrorCode.INVALID_ARGUMENTS, "")) == 3


def test_s26_exit_code_permission_denied() -> None:
    assert exit_code_for(BiomeError(ErrorCode.PERMISSION_DENIED, "")) == 4


def test_s26_exit_code_timeout() -> None:
    assert exit_code_for(BiomeError(ErrorCode.TIMEOUT, "")) == 5


def test_s26_exit_code_connection_lost() -> None:
    assert exit_code_for(BiomeError(ErrorCode.CONNECTION_LOST, "")) == 6


def test_s26_exit_code_internal_error() -> None:
    assert exit_code_for(BiomeError(ErrorCode.INTERNAL_ERROR, "")) == 1


def test_s26_exit_code_cancelled() -> None:
    assert exit_code_for(BiomeError(ErrorCode.CANCELLED, "")) == 130
