"""S1, S4, S5: TOOL parser tests."""
from __future__ import annotations

import pytest

from biome_mcp.dsl.parser import parse_tools

_MINIMAL = """\
TOOL scene.inspect "Inspect scene hierarchy" read BATCHABLE
  PARAM path REQUIRED str "object path filter"
  PARAM depth int DEFAULT 3 "max tree depth"
END
"""

_WRITE_BLAST = """\
TOOL scene.set_active "Activate object" write BLAST 2
  PARAM path REQUIRED str "object path"
  PARAM active REQUIRED bool "new active state"
END
"""


def test_s1_parse_basic_tool() -> None:
    tools = parse_tools(_MINIMAL)
    assert len(tools) == 1
    t = tools[0]
    assert t.name == "scene.inspect"
    assert t.summary == "Inspect scene hierarchy"
    assert t.effect == "read"
    assert t.batchable is True
    assert t.blast_radius == 0
    assert len(t.params) == 2


def test_s1_param_fields() -> None:
    t = parse_tools(_MINIMAL)[0]
    p0, p1 = t.params
    assert p0.name == "path"
    assert p0.param_type == "str"
    assert p0.required is True
    assert p0.default is None
    assert p1.name == "depth"
    assert p1.required is False
    assert p1.default == "3"


def test_s4_namespace_from_dot() -> None:
    t = parse_tools(_MINIMAL)[0]
    assert t.namespace == "scene"


def test_s4_namespace_no_dot() -> None:
    src = 'TOOL inspect "Inspect" read\nEND'
    t = parse_tools(src)[0]
    assert t.namespace == "inspect"


def test_s5_batchable_and_blast() -> None:
    t = parse_tools(_WRITE_BLAST)[0]
    assert t.batchable is False
    assert t.blast_radius == 2
    assert t.effect == "write"


def test_multi_tools() -> None:
    tools = parse_tools(_MINIMAL + "\n" + _WRITE_BLAST)
    assert len(tools) == 2


def test_nested_tool_raises() -> None:
    src = 'TOOL a "x" read\nTOOL b "y" read\nEND'
    with pytest.raises(SyntaxError, match="nested"):
        parse_tools(src)


def test_unknown_effect_raises() -> None:
    src = 'TOOL a "x" destroy\nEND'
    with pytest.raises(SyntaxError, match="effect"):
        parse_tools(src)


def test_missing_end_raises() -> None:
    src = 'TOOL a "x" read\n  PARAM p REQUIRED str "desc"'
    with pytest.raises(SyntaxError, match="EOF"):
        parse_tools(src)


def test_end_without_tool_raises() -> None:
    with pytest.raises(SyntaxError, match="END without"):
        parse_tools("END")


def test_blast_non_int_raises() -> None:
    src = 'TOOL a "x" write BLAST abc\nEND'
    with pytest.raises(SyntaxError, match="BLAST"):
        parse_tools(src)


def test_default_int_invalid_raises() -> None:
    src = 'TOOL a "x" read\n  PARAM p int DEFAULT hello "desc"\nEND'
    with pytest.raises(SyntaxError, match="integer"):
        parse_tools(src)


def test_default_bool_invalid_raises() -> None:
    src = 'TOOL a "x" read\n  PARAM p bool DEFAULT maybe "desc"\nEND'
    with pytest.raises(SyntaxError, match="true/false"):
        parse_tools(src)


def test_default_list_rejected() -> None:
    src = 'TOOL a "x" read\n  PARAM p list DEFAULT x "desc"\nEND'
    with pytest.raises(SyntaxError, match="list"):
        parse_tools(src)


def test_comments_and_blank_lines() -> None:
    src = "# comment\n\n" + _MINIMAL
    assert len(parse_tools(src)) == 1
