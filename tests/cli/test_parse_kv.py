"""S4-S7: parse_kv coercion rules."""
from __future__ import annotations

import pytest

from biome_mcp.cli.generic import parse_kv


def test_s4_str_and_int() -> None:
    """S4: basic str and int coercion."""
    assert parse_kv(["path=x", "count=3"]) == {"path": "x", "count": 3}


def test_s4_float() -> None:
    assert parse_kv(["val=3.14"]) == {"val": 3.14}


def test_s4_empty() -> None:
    assert parse_kv([]) == {}


def test_s5_bool_true_variants() -> None:
    """S5: true/yes become True (case-insensitive). 0/1 stay int."""
    assert parse_kv(["f=true"]) == {"f": True}
    assert parse_kv(["f=True"]) == {"f": True}
    assert parse_kv(["f=yes"]) == {"f": True}


def test_s5_bool_false_variants() -> None:
    """S5: false/no become False (case-insensitive). 0/1 stay int."""
    assert parse_kv(["f=false"]) == {"f": False}
    assert parse_kv(["f=False"]) == {"f": False}
    assert parse_kv(["f=no"]) == {"f": False}


def test_s5_numeric_01_are_int_not_bool() -> None:
    """0 and 1 are int, not bool — depth=1 must be 1, not True."""
    result = parse_kv(["depth=1"])
    assert result == {"depth": 1}
    assert type(result["depth"]) is int
    result = parse_kv(["depth=0"])
    assert result == {"depth": 0}
    assert type(result["depth"]) is int


def test_s6_no_equals_raises() -> None:
    """S6: token without = raises ValueError."""
    with pytest.raises(ValueError, match="="):
        parse_kv(["noeq"])


def test_s7_multiline_value() -> None:
    """S7: multiline string value preserved as-is."""
    result = parse_kv(["script=line1\nline2"])
    assert result == {"script": "line1\nline2"}
