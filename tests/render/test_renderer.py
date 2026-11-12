"""Stage 3: PlainTextRenderer tests."""

import json

from biome_mcp.models.result import CommandResult
from biome_mcp.render.profiles import COMPACT, RenderProfile
from biome_mcp.render.renderer import PlainTextRenderer


def test_render_ok_result():
    r = CommandResult.ok("scene loaded")
    text = PlainTextRenderer().render(r)
    assert text == "scene loaded"


def test_render_ok_with_data():
    r = CommandResult.ok("found", data={"count": 3})
    text = PlainTextRenderer().render(r)
    assert "found" in text
    assert '"count": 3' in text


def test_render_error_result():
    r = CommandResult.error("E_TIMEOUT", "timed out")
    text = PlainTextRenderer().render(r)
    assert "[failed]" in text
    assert "timed out" in text
    assert "E_TIMEOUT" in text


def test_render_compact_omits_data():
    r = CommandResult.ok("found", data={"count": 3})
    text = PlainTextRenderer(COMPACT).render(r)
    assert "found" in text
    assert "count" not in text


def test_render_budget_truncates():
    profile = RenderProfile(name="tiny", max_chars=20)
    r = CommandResult.ok("a" * 100)
    text = PlainTextRenderer(profile).render(r)
    assert len(text) <= 20
    assert text.endswith("[truncated]")


def test_render_batch():
    results = [CommandResult.ok("one"), CommandResult.ok("two")]
    text = PlainTextRenderer().render_batch(results)
    assert "one" in text
    assert "two" in text
    assert "\n" in text


def test_project_fields_keeps_only_listed_keys():
    text = json.dumps({"a": 1, "b": 2, "c": 3})
    out = PlainTextRenderer().project_fields(text, ["a", "c"])
    assert json.loads(out) == {"a": 1, "c": 3}


def test_project_fields_none_is_passthrough():
    text = '{"a": 1}'
    out = PlainTextRenderer().project_fields(text, None)
    assert out == text


def test_project_fields_non_json_is_passthrough():
    text = "plain text, not json"
    out = PlainTextRenderer().project_fields(text, ["a"])
    assert out == text


def test_strip_defaults_removes_listed_keys():
    text = json.dumps({"a": 1, "b": 2})
    out = PlainTextRenderer().strip_defaults(text, frozenset({"b"}))
    assert json.loads(out) == {"a": 1}


def test_strip_defaults_no_match_keeps_all():
    text = json.dumps({"a": 1})
    out = PlainTextRenderer().strip_defaults(text, frozenset({"z"}))
    assert json.loads(out) == {"a": 1}


def test_strip_defaults_non_json_is_passthrough():
    text = "plain text, not json"
    out = PlainTextRenderer().strip_defaults(text, frozenset({"a"}))
    assert out == text
