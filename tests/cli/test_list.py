"""S10-S16: list handler with filters."""
from __future__ import annotations

import json

from tests.cli.conftest import run_cmd


def test_s10_list_grouped_by_namespace() -> None:
    """S10: default list groups tools by namespace."""
    out, err, code = run_cmd(["list"])
    assert code == 0
    assert "scene_inspect" in out
    assert "animator" in out
    # Grouped: namespace header should appear
    assert "scene" in out


def test_s11_list_flat() -> None:
    """S11: --flat bypasses namespace grouping."""
    out, err, code = run_cmd(["list", "--flat"])
    assert code == 0
    assert "scene_inspect" in out
    assert "animator" in out


def test_s12_list_ns_filter() -> None:
    """S12: --ns scene shows only scene-prefixed tools."""
    out, err, code = run_cmd(["list", "--ns", "scene"])
    assert code == 0
    assert "scene_inspect" in out
    assert "scene_diff" in out
    assert "animator" not in out


def test_s13_list_effect_read() -> None:
    """S13: --effect read shows only read tools."""
    out, err, code = run_cmd(["list", "--effect", "read"])
    assert code == 0
    assert "scene_inspect" in out
    assert "scene_diff" in out
    assert "get_hierarchy" in out
    assert "animator" not in out  # write


def test_s13_list_effect_write() -> None:
    """S13: --effect write shows write/idempotent_write/delete tools."""
    out, err, code = run_cmd(["list", "--effect", "write"])
    assert code == 0
    assert "animator" in out
    assert "collider_mesh" in out
    assert "scene_inspect" not in out  # read


def test_s14_list_grep_name() -> None:
    """S14: --grep filters by name substring."""
    out, err, code = run_cmd(["list", "--grep", "collider"])
    assert code == 0
    assert "collider_mesh" in out
    assert "animator" not in out


def test_s14_list_grep_description() -> None:
    """S14: --grep filters by description substring (case-insensitive)."""
    out, err, code = run_cmd(["list", "--grep", "state machine"])
    assert code == 0
    assert "animator" in out
    assert "scene_inspect" not in out


def test_s15_list_json_no_input_schema() -> None:
    """S15: --json outputs array without input_schema."""
    out, err, code = run_cmd(["list", "--json"])
    assert code == 0
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert "name" in item
        assert "input_schema" not in item  # minimal projection


def test_s16_filters_and_compose() -> None:
    """S16: --ns and --effect AND-compose (scene + write = no match in FAKE_TOOLS)."""
    out, err, code = run_cmd(["list", "--ns", "scene", "--effect", "write"])
    assert code == 0
    # All scene tools in FAKE_TOOLS are "read", so no matches
    assert "scene_inspect" not in out
    assert "animator" not in out
