"""Batch text parser — adapted from biome-browser-mcp."""

from __future__ import annotations

import json
import re
from typing import Any

from biome_mcp.batch.lexer import (
    split_key_value,
    split_label_and_rest,
    split_name_and_rest,
    tokenize_args,
)
from biome_mcp.batch.model import (
    BatchDocument,
    BatchLimits,
    LexicalKind,
    ParsedArg,
    ParsedCommand,
)
from biome_mcp.errors import BiomeError, ErrorCode

_NUMBER_RE = re.compile(r"-?(0|[1-9]\d*)(\.\d+)?([eE][+-]?\d+)?")
_BARE_FORBIDDEN_RE = re.compile(r'[\s"\'\[\]{}\x00-\x1f;|`]|&&|\$\(')
_AUTO_LABEL_RE = re.compile(r"s(\d+)")


_DEFAULT_LIMITS = BatchLimits()


def parse_batch(text: str, *, limits: BatchLimits = _DEFAULT_LIMITS) -> BatchDocument:
    if len(text.encode("utf-8")) > limits.max_bytes:
        raise BiomeError(ErrorCode.INVALID_ARGUMENTS, "batch exceeds byte limit")
    lines = text.splitlines()
    commands: list[ParsedCommand] = []
    for line_no, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        ordinal = len(commands) + 1
        if ordinal > limits.max_commands:
            raise BiomeError(ErrorCode.INVALID_ARGUMENTS, "too many commands")
        commands.append(_parse_line(stripped, line_no, ordinal))
    if not commands:
        raise BiomeError(ErrorCode.INVALID_ARGUMENTS, "batch has no commands")
    _check_labels(commands)
    return BatchDocument(commands=tuple(commands), source_lines=tuple(lines))


def _check_labels(commands: list[ParsedCommand]) -> None:
    seen: set[str] = set()
    for cmd in commands:
        if not cmd.explicit_label:
            continue
        m = _AUTO_LABEL_RE.fullmatch(cmd.step_id)
        if (m is not None and int(m.group(1)) != cmd.ordinal) or cmd.step_id in seen:
            raise BiomeError(
                ErrorCode.INVALID_ARGUMENTS, f"label {cmd.step_id!r} clash"
            )
        seen.add(cmd.step_id)


def _parse_line(stripped: str, line_no: int, ordinal: int) -> ParsedCommand:
    label, rest = split_label_and_rest(stripped)
    name, args_text = split_name_and_rest(rest, line_no)
    args: list[ParsedArg] = []
    seen_keys: set[str] = set()
    for token in tokenize_args(args_text):
        key, value_text = split_key_value(token, line_no)
        if key in seen_keys:
            raise BiomeError(
                ErrorCode.INVALID_ARGUMENTS, f"duplicate key {key!r} (line {line_no})"
            )
        seen_keys.add(key)
        kind, value = _classify_value(value_text)
        args.append(ParsedArg(key=key, kind=kind, raw=value_text, value=value))
    return ParsedCommand(
        step_id=label if label is not None else f"s{ordinal}",
        ordinal=ordinal, line_no=line_no, name=name,
        args=tuple(args), explicit_label=label is not None,
    )


def _classify_value(token: str) -> tuple[LexicalKind, Any]:
    if token == "true":
        return LexicalKind.BOOLEAN, True
    if token == "false":
        return LexicalKind.BOOLEAN, False
    if token == "null":
        return LexicalKind.NULL, None
    if _NUMBER_RE.fullmatch(token):
        if any(c in token for c in ".eE"):
            return LexicalKind.NUMBER, float(token)
        return LexicalKind.NUMBER, int(token)
    if token.startswith('"'):
        try:
            value = json.loads(token)
        except json.JSONDecodeError as exc:
            raise BiomeError(ErrorCode.INVALID_ARGUMENTS, str(exc)) from exc
        return LexicalKind.QUOTED, value
    if token.startswith("[") or token.startswith("{"):
        try:
            value = json.loads(token)
        except json.JSONDecodeError as exc:
            raise BiomeError(ErrorCode.INVALID_ARGUMENTS, str(exc)) from exc
        return LexicalKind.JSON_LITERAL, value
    if _BARE_FORBIDDEN_RE.search(token):
        raise BiomeError(ErrorCode.INVALID_ARGUMENTS, f"bad bare value {token!r}")
    return LexicalKind.BARE, token
