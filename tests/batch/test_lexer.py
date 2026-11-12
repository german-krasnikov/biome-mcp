"""Stage 2: Batch lexer tests."""

import pytest

from biome_mcp.batch.lexer import (
    split_key_value,
    split_label_and_rest,
    split_name_and_rest,
    tokenize_args,
)
from biome_mcp.errors import BiomeError


def test_tokenize_simple():
    tokens = tokenize_args('key=value other=123')
    assert tokens == ["key=value", "other=123"]


def test_tokenize_quoted():
    tokens = tokenize_args('data="hello world" x=1')
    assert tokens == ['data="hello world"', "x=1"]


def test_tokenize_json():
    tokens = tokenize_args('data={"a": 1, "b": 2} x=3')
    assert tokens == ['data={"a": 1, "b": 2}', "x=3"]


def test_tokenize_nested_brackets():
    tokens = tokenize_args('data=[1, [2, 3]]')
    assert tokens == ["data=[1, [2, 3]]"]


def test_split_label_and_rest():
    label, rest = split_label_and_rest("my_step: core.do_thing x=1")
    assert label == "my_step"
    assert rest == "core.do_thing x=1"


def test_split_label_none():
    label, rest = split_label_and_rest("core.do_thing x=1")
    assert label is None
    assert rest == "core.do_thing x=1"


def test_split_name_and_rest():
    name, rest = split_name_and_rest("core.do_thing x=1", 1)
    assert name == "core.do_thing"
    assert rest == "x=1"


def test_split_key_value_ok():
    key, val = split_key_value("path=/tmp/foo", 1)
    assert key == "path"
    assert val == "/tmp/foo"


def test_split_key_value_no_equals():
    with pytest.raises(BiomeError):
        split_key_value("badtoken", 1)
