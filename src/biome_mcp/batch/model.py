"""Batch document model — parser output shape."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class LexicalKind(StrEnum):
    BARE = "bare"
    QUOTED = "quoted"
    BOOLEAN = "boolean"
    NULL = "null"
    NUMBER = "number"
    JSON_LITERAL = "json_literal"


@dataclass(frozen=True, slots=True)
class ParsedArg:
    key: str
    kind: LexicalKind
    raw: str
    value: Any


@dataclass(frozen=True, slots=True)
class ParsedCommand:
    step_id: str
    ordinal: int
    line_no: int
    name: str
    args: tuple[ParsedArg, ...]
    explicit_label: bool


@dataclass(frozen=True, slots=True)
class BatchDocument:
    commands: tuple[ParsedCommand, ...]
    source_lines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BatchLimits:
    max_bytes: int = 65536
    max_commands: int = 128
    max_json_depth: int = 16

    def __post_init__(self) -> None:
        for name in ("max_bytes", "max_commands", "max_json_depth"):
            if getattr(self, name) <= 0:
                raise ValueError(f"BatchLimits.{name} must be > 0")
