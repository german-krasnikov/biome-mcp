"""S2, S3, S6: codegen tests."""
from __future__ import annotations

from biome_mcp.dsl.codegen import gen_descriptors, gen_help_text, gen_schema_init
from biome_mcp.dsl.parser import parse_tools
from biome_mcp.schema_registry import SchemaRegistry

_SRC = """\
TOOL scene.inspect "Inspect scene hierarchy" read BATCHABLE
  PARAM path REQUIRED str "object path filter"
  PARAM depth int DEFAULT 3 "max tree depth"
END

TOOL scene.set_active "Activate object" write BLAST 2
  PARAM path REQUIRED str "object path"
  PARAM active REQUIRED bool "new active state"
END
"""


def _tools():
    return parse_tools(_SRC)


def test_s2_descriptors_required_param() -> None:
    out = gen_descriptors(_tools())
    assert "SCENE_INSPECT = CommandDescriptor(" in out
    assert 'name="scene.inspect"' in out
    assert 'namespace="scene"' in out
    assert "required=True" in out
    assert "required=False" in out
    assert "CommandEffect.READ" in out


def test_s2_schema_required_list() -> None:
    out = gen_schema_init(_tools())
    assert '"required": ["path"]' in out


def test_s3_default_in_descriptor() -> None:
    out = gen_descriptors(_tools())
    assert "default=3" in out


def test_s3_schema_no_default_in_required() -> None:
    out = gen_schema_init(_tools())
    assert 'registry.capture("scene.inspect"' in out
    assert '"integer"' in out


def test_s5_batchable_blast_roundtrip() -> None:
    out = gen_descriptors(_tools())
    assert "batchable=True" in out
    assert "batchable=False" in out
    assert "blast_radius=2" in out
    assert "blast_radius=0" in out


def test_s6_help_text_format() -> None:
    out = gen_help_text(_tools())
    assert "== scene.inspect ==" in out
    assert "Params: path*:str depth:int=3" in out
    assert "[WRITE]" in out


def test_s6_help_matches_schema_registry() -> None:
    """Generated help format matches SchemaRegistry.format_text()."""
    tools = _tools()
    schema_out = gen_schema_init(tools)

    registry = SchemaRegistry()
    ns: dict = {}
    exec(schema_out, ns)  # noqa: S102
    ns["init"](registry)

    reg_text = registry.format_text(["scene.inspect"])
    help_text = gen_help_text(tools)

    help_inspect = help_text.split("\n\n")[0]
    assert "== scene.inspect ==" in reg_text
    assert "== scene.inspect ==" in help_inspect
    assert "path*:str" in reg_text
    assert "path*:str" in help_inspect


def test_escape_quotes_in_summary() -> None:
    src = """TOOL a.b "Use 'inspect' mode" read\nEND"""
    tools = parse_tools(src)
    out = gen_descriptors(tools)
    assert "\\'inspect\\'" not in out  # single quotes don't need escape
    assert "Use 'inspect' mode" in out


def test_escape_double_quotes_in_summary() -> None:
    src = 'TOOL a.b "Say \\"hello\\"" read\nEND'
    tools = parse_tools(src)
    desc = gen_descriptors(tools)
    assert '\\"hello\\"' in desc


def test_descriptors_importable(tmp_path) -> None:
    """Generated descriptor file is valid Python."""
    tools = _tools()
    code = gen_descriptors(tools)
    f = tmp_path / "tool_descriptors.py"
    f.write_text(code, encoding="utf-8")
    compiled = compile(code, str(f), "exec")
    assert compiled is not None


def test_schema_init_callable(tmp_path) -> None:
    """Generated schema init can be exec'd with a registry."""
    tools = _tools()
    code = gen_schema_init(tools)
    ns: dict = {}
    exec(code, ns)  # noqa: S102
    registry = SchemaRegistry()
    ns["init"](registry)
    assert registry.get_full("scene.inspect") is not None
    assert registry.get_full("scene.set_active") is not None
