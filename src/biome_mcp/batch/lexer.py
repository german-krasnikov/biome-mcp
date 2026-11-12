"""Batch tokenizer — adapted from biome-browser-mcp."""

from __future__ import annotations

import re

from biome_mcp.errors import BiomeError, ErrorCode

_LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*): ")
_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*")
_KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def split_label_and_rest(line: str) -> tuple[str | None, str]:
    match = _LABEL_RE.match(line)
    if match is None:
        return None, line
    return match.group(1), line[match.end():]


def split_name_and_rest(rest: str, line_no: int) -> tuple[str, str]:
    match = _NAME_RE.match(rest)
    if match is None:
        raise BiomeError(ErrorCode.INVALID_ARGUMENTS, f"expected command name (line {line_no})")
    name = match.group(0)
    remainder = rest[match.end():]
    if remainder and not remainder.startswith(" "):
        raise BiomeError(
            ErrorCode.INVALID_ARGUMENTS,
            f"expected space after command name {name!r} (line {line_no})",
        )
    return name, remainder.strip()


def tokenize_args(text: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    in_quotes = False
    escape_next = False
    depth = 0
    for ch in text:
        if in_quotes:
            current.append(ch)
            if escape_next:
                escape_next = False
            elif ch == "\\":
                escape_next = True
            elif ch == '"':
                in_quotes = False
            continue
        if ch == '"':
            in_quotes = True
            current.append(ch)
        elif ch in "[{":
            depth += 1
            current.append(ch)
        elif ch in "]}":
            depth = max(depth - 1, 0)
            current.append(ch)
        elif ch.isspace() and depth == 0:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(ch)
    if current:
        tokens.append("".join(current))
    return tokens


def split_key_value(token: str, line_no: int) -> tuple[str, str]:
    index = token.find("=")
    key = token[:index] if index > 0 else ""
    if index <= 0 or _KEY_RE.fullmatch(key) is None:
        raise BiomeError(
            ErrorCode.INVALID_ARGUMENTS, f"bad argument {token!r} (line {line_no})"
        )
    return key, token[index + 1:]
