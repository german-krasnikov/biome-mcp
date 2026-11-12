"""record_runtime: parser/formatter for wire records `[head|]key=value|key=value`."""

from __future__ import annotations

from typing import NamedTuple

from biome_mcp.record_runtime import formatter, parser


class Sample(NamedTuple):
    epoch: int
    state: str
    err: str | None = None
    dur: float | None = None
    flag: bool | None = None


FIELDS = (
    ("epoch", "int"),
    ("state", "word"),
    ("err", "text", "optional"),
    ("dur", "float1", "optional"),
    ("flag", "bool", "optional"),
)

parse_sample = parser(Sample, FIELDS)
format_sample = formatter(FIELDS)
parse_sample_headed = parser(Sample, FIELDS, head="sample")
format_sample_headed = formatter(FIELDS, head="sample")


def test_parser_parses_required_fields_only():
    result = parse_sample("epoch=1|state=ok")
    assert result == Sample(epoch=1, state="ok")


def test_parser_parses_optional_fields():
    result = parse_sample("epoch=1|state=ok|err=boom|dur=2.5|flag=true")
    assert result == Sample(epoch=1, state="ok", err="boom", dur=2.5, flag=True)


def test_parser_returns_none_when_required_field_missing():
    assert parse_sample("state=ok") is None


def test_parser_returns_none_on_bad_type():
    assert parse_sample("epoch=notanint|state=ok") is None


def test_parser_returns_none_on_duplicate_key():
    assert parse_sample("epoch=1|epoch=2|state=ok") is None


def test_parser_returns_none_on_non_string_input():
    assert parse_sample(None) is None
    assert parse_sample(123) is None


def test_parser_ignores_unknown_keys():
    result = parse_sample("epoch=1|state=ok|extra=whatever")
    assert result == Sample(epoch=1, state="ok")


def test_parser_head_mismatch_returns_none():
    assert parse_sample_headed("other|epoch=1|state=ok") is None


def test_parser_head_match_strips_lead_word():
    result = parse_sample_headed("sample|epoch=1|state=ok")
    assert result == Sample(epoch=1, state="ok")


def test_formatter_omits_none_optionals():
    line = format_sample(epoch=1, state="ok")
    assert line == "epoch=1|state=ok"


def test_formatter_includes_present_optionals():
    line = format_sample(epoch=1, state="ok", flag=False, dur=1.0)
    assert line == "epoch=1|state=ok|dur=1.0|flag=false"


def test_formatter_prefixes_head():
    line = format_sample_headed(epoch=1, state="ok")
    assert line == "sample|epoch=1|state=ok"


def test_roundtrip_parse_then_format():
    original = Sample(epoch=7, state="busy", err="x", dur=0.3, flag=True)
    line = format_sample(**original._asdict())
    assert parse_sample(line) == original
