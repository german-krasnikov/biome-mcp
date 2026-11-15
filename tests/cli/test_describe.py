"""S17-S21: describe handler."""
from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout

from biome_mcp.cli.generic import make_describe_handler
from biome_mcp.schema_registry import SchemaRegistry
from tests.cli.conftest import FakeToolProvider, run_cmd


def test_s17_describe_known_tool() -> None:
    """S17: describe known tool prints name + params."""
    out, err, code = run_cmd(["describe", "animator"])
    assert code == 0
    assert "animator" in out
    assert "action" in out  # param from input_schema


def test_s17_describe_shows_header() -> None:
    """S17: describe output has == name == header."""
    out, err, code = run_cmd(["describe", "animator"])
    assert "== animator ==" in out


def test_s18_describe_unknown_exit2() -> None:
    """S18: describe unknown tool → exit 2 + hint to stderr."""
    out, err, code = run_cmd(["describe", "nonexistent_tool"])
    assert code == 2
    assert "nonexistent_tool" in err or "not found" in err


def test_s19_describe_json() -> None:
    """S19: --json outputs full ToolInfo including input_schema."""
    out, err, code = run_cmd(["describe", "animator", "--json"])
    assert code == 0
    data = json.loads(out)
    assert data["name"] == "animator"
    assert "input_schema" in data


def test_s20_describe_with_registry_uses_format_text() -> None:
    """S20: when SchemaRegistry provided, uses format_text output."""
    registry = SchemaRegistry()
    registry.capture(
        "animator",
        {"properties": {"action": {"type": "string"}}, "required": ["action"]},
        "Animator Controller",
    )
    provider = FakeToolProvider()
    handler = make_describe_handler(provider, registry=registry)

    out_buf, err_buf = io.StringIO(), io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        code = handler(["animator"])

    out = out_buf.getvalue()
    assert code == 0
    assert "== animator ==" in out


def test_s21_describe_without_registry_fallback() -> None:
    """S21: without registry, falls back to ToolInfo rendering."""
    out, err, code = run_cmd(["describe", "animator"])
    assert code == 0
    assert "animator" in out
    assert len(out.strip()) > 0


def test_s18_describe_no_name_exit3() -> None:
    """m6: describe with no tool name → exit 3."""
    out, err, code = run_cmd(["describe"])
    assert code == 3
    assert "requires" in err
