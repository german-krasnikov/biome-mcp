"""SchemaRegistry: capture/get_full/format_text — a lazy tool-schema registry."""

from __future__ import annotations

from biome_mcp.schema_registry import STUB_SCHEMA, SchemaRegistry


def _make_schema(props: dict | None = None, required: list | None = None) -> dict:
    schema: dict = {"type": "object"}
    if props:
        schema["properties"] = props
    if required:
        schema["required"] = required
    return schema


def test_capture_and_get_full_roundtrip():
    reg = SchemaRegistry()
    schema = _make_schema({"path": {"type": "string"}}, ["path"])
    reg.capture("my_tool", schema, "A tool that does stuff")
    result = reg.get_full("my_tool")
    assert result is not None
    assert result["inputSchema"] == schema
    assert result["description"] == "A tool that does stuff"


def test_get_full_unknown_returns_none():
    reg = SchemaRegistry()
    assert reg.get_full("nonexistent_tool") is None


def test_stub_schema_is_minimal():
    assert STUB_SCHEMA == {"type": "object", "properties": {}, "additionalProperties": False}


def test_format_text_single_tool():
    reg = SchemaRegistry()
    schema = _make_schema(
        {"path": {"type": "string"}, "value": {"type": "number"}},
        ["path"],
    )
    reg.capture("set_prop", schema, "Set a property")
    text = reg.format_text(["set_prop"])
    assert "== set_prop ==" in text
    assert "Set a property" in text
    assert "path" in text
    assert "value" in text


def test_format_text_multiple_tools():
    reg = SchemaRegistry()
    reg.capture("tool_a", _make_schema({"x": {"type": "string"}}, ["x"]), "Tool A")
    reg.capture("tool_b", _make_schema({"y": {"type": "integer"}}), "Tool B")
    text = reg.format_text(["tool_a", "tool_b"])
    assert "== tool_a ==" in text
    assert "== tool_b ==" in text


def test_format_text_unknown_skipped():
    reg = SchemaRegistry()
    reg.capture("tool_a", _make_schema({"x": {"type": "string"}}), "Tool A")
    text = reg.format_text(["tool_a", "ghost_tool"])
    assert "== tool_a ==" in text
    assert "ghost_tool" not in text


def test_known_names_after_capture():
    reg = SchemaRegistry()
    reg.capture("alpha", _make_schema(), "Alpha")
    reg.capture("beta", _make_schema(), "Beta")
    names = reg.known_names()
    assert "alpha" in names
    assert "beta" in names


def test_capture_idempotent():
    reg = SchemaRegistry()
    schema1 = _make_schema({"a": {"type": "string"}})
    schema2 = _make_schema({"b": {"type": "integer"}})
    reg.capture("dup_tool", schema1, "First")
    reg.capture("dup_tool", schema2, "Second")
    result = reg.get_full("dup_tool")
    assert result["inputSchema"] == schema2
    assert result["description"] == "Second"


def test_format_text_plain_not_json():
    reg = SchemaRegistry()
    reg.capture("my_tool", _make_schema({"path": {"type": "string"}}, ["path"]), "Desc")
    text = reg.format_text(["my_tool"])
    assert "{" not in text


def test_format_text_required_marked_with_star():
    reg = SchemaRegistry()
    schema = _make_schema(
        {"path": {"type": "string"}, "count": {"type": "integer"}},
        ["path"],
    )
    reg.capture("my_tool", schema, "Desc")
    text = reg.format_text(["my_tool"])
    assert "path*" in text
    assert "count" in text
    assert "count*" not in text
    assert "Required:" not in text


def test_format_text_enum_values_listed():
    reg = SchemaRegistry()
    schema = _make_schema(
        {"action": {"type": "string", "enum": ["get", "set", "delete"]}},
        ["action"],
    )
    reg.capture("crud_tool", schema, "CRUD")
    text = reg.format_text(["crud_tool"])
    assert "get" in text
    assert "set" in text
    assert "delete" in text


def test_annotations_preserved():
    reg = SchemaRegistry()
    schema = _make_schema({"path": {"type": "string"}})
    annotations = {"readOnlyHint": True}
    reg.capture("safe_tool", schema, "Safe read-only tool", annotations=annotations)
    result = reg.get_full("safe_tool")
    assert result is not None
    assert result.get("annotations") == annotations


def test_format_text_empty_schema_no_params_line():
    reg = SchemaRegistry()
    reg.capture("empty_tool", {"type": "object"}, "No params tool")
    text = reg.format_text(["empty_tool"])
    assert "== empty_tool ==" in text
    assert "No params tool" in text
    assert "Params:" not in text


def test_format_text_nested_object_shows_type_object():
    reg = SchemaRegistry()
    schema = _make_schema({
        "config": {
            "type": "object",
            "properties": {"x": {"type": "number"}},
        }
    })
    reg.capture("nested_tool", schema, "Nested prop tool")
    text = reg.format_text(["nested_tool"])
    assert "config" in text
    assert "object" in text
    assert "{" not in text


def test_format_text_empty_list_returns_empty_string():
    reg = SchemaRegistry()
    reg.capture("some_tool", _make_schema({"x": {"type": "string"}}), "Desc")
    text = reg.format_text([])
    assert text == ""
