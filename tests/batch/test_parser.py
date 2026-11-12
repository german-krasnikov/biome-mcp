"""Stage 2: Batch parser tests."""

import pytest

from biome_mcp.batch.parser import parse_batch
from biome_mcp.errors import BiomeError


def test_parse_single_command():
    doc = parse_batch("scene.inspect path=/Game")
    assert len(doc.commands) == 1
    cmd = doc.commands[0]
    assert cmd.name == "scene.inspect"
    assert cmd.args[0].key == "path"
    assert cmd.args[0].value == "/Game"
    assert cmd.step_id == "s1"
    assert not cmd.explicit_label


def test_parse_multi_command():
    text = "scene.inspect path=/a\nscene.create name=obj"
    doc = parse_batch(text)
    assert len(doc.commands) == 2
    assert doc.commands[0].name == "scene.inspect"
    assert doc.commands[1].name == "scene.create"
    assert doc.commands[1].step_id == "s2"


def test_parse_labels():
    text = "step1: scene.inspect path=/a\nstep2: scene.create name=obj"
    doc = parse_batch(text)
    assert doc.commands[0].step_id == "step1"
    assert doc.commands[0].explicit_label is True
    assert doc.commands[1].step_id == "step2"


def test_parse_comments_and_blank_lines():
    text = "# comment\n\nscene.inspect path=/a\n# another"
    doc = parse_batch(text)
    assert len(doc.commands) == 1


def test_parse_empty_raises():
    with pytest.raises(BiomeError):
        parse_batch("")

    with pytest.raises(BiomeError):
        parse_batch("# only comments")


def test_parse_boolean_and_number():
    doc = parse_batch("test.cmd flag=true count=42 ratio=3.14")
    args = {a.key: a.value for a in doc.commands[0].args}
    assert args["flag"] is True
    assert args["count"] == 42
    assert args["ratio"] == 3.14


def test_parse_quoted_string():
    doc = parse_batch('test.cmd msg="hello world"')
    assert doc.commands[0].args[0].value == "hello world"


def test_parse_json_literal():
    doc = parse_batch('test.cmd data={"key":"val"}')
    assert doc.commands[0].args[0].value == {"key": "val"}
