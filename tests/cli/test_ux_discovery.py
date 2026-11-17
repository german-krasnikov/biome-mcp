"""Tests for CLI UX discovery: fuzzy, namespace, --help, required args, dry-run."""
from __future__ import annotations

from biome_mcp.models.result import CommandResult
from tests.cli.conftest import run_cmd


def test_fuzzy_suggestion_on_typo() -> None:
    """Typo in tool name → 'Did you mean' suggestion."""
    out, err, code = run_cmd(["scene_inpsect"])
    assert code != 0
    assert "Did you mean" in err
    assert "scene_inspect" in err


def test_no_suggestion_for_total_garbage() -> None:
    """Completely unknown name → no suggestion, just error."""
    out, err, code = run_cmd(["zzzzzzzzz"])
    assert code != 0
    assert "not found" in err
    assert "Did you mean" not in err


def test_tool_help_flag() -> None:
    """'animator --help' → shows describe output."""
    out, err, code = run_cmd(["animator", "--help"])
    assert code == 0
    assert "animator" in out.lower()
    assert "Parameters" in out


def test_tool_h_flag() -> None:
    """'animator -h' → same as --help."""
    out, err, code = run_cmd(["animator", "-h"])
    assert code == 0
    assert "animator" in out.lower()


def test_namespace_prefix_lists_tools() -> None:
    """'scene' (no args, 2+ tools in ns) → list scene.* tools."""
    out, err, code = run_cmd(["scene"])
    assert code == 0
    assert "scene_inspect" in out
    assert "scene_diff" in out


def test_namespace_prefix_one_tool_falls_through_to_call() -> None:
    """Namespace prefix with only 1 match → not listed, falls to implicit call."""
    results = {"collider_mesh": CommandResult.ok("mesh ok")}
    out, err, code = run_cmd(["collider"], results=results)
    assert code != 0  # collider is not an exact tool name, falls to call → not found


def test_required_args_validation() -> None:
    """Call tool missing required args → helpful error with example."""
    out, err, code = run_cmd(["call", "animator"])
    assert code == 3
    assert "missing required" in err
    assert "action" in err
    assert "path" in err
    assert "example" in err.lower()


def test_dry_run() -> None:
    """--dry-run prints args without calling."""
    results = {"scene_inspect": CommandResult.ok("should not see this")}
    out, err, code = run_cmd(
        ["call", "scene_inspect", "depth=5", "--dry-run"], results=results,
    )
    assert code == 0
    assert "[dry-run]" in out
    assert "scene_inspect" in out
    assert "should not see this" not in out


def test_dry_run_implicit() -> None:
    """--dry-run works with implicit call too."""
    results = {"scene_inspect": CommandResult.ok("nope")}
    out, err, code = run_cmd(
        ["scene_inspect", "depth=5", "--dry-run"], results=results,
    )
    assert code == 0
    assert "[dry-run]" in out


def test_dry_run_blocked_by_missing_required() -> None:
    """--dry-run still validates required args first."""
    out, err, code = run_cmd(["animator", "--dry-run"])
    assert code == 3
    assert "missing required" in err
