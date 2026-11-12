"""CommandResult — typed result with status, text, and optional data."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class CommandStatus(StrEnum):
    OK = "ok"
    INVALID_ARGS = "invalid_args"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CommandResult:
    status: CommandStatus
    text: str
    data: Any = None
    complete: bool = True
    error_code: str | None = None

    @classmethod
    def ok(cls, text: str, data: Any = None) -> CommandResult:
        return cls(status=CommandStatus.OK, text=text, data=data)

    @classmethod
    def error(cls, code: str, text: str) -> CommandResult:
        return cls(status=CommandStatus.FAILED, text=text, error_code=code)

    @classmethod
    def cancelled(cls, text: str = "") -> CommandResult:
        return cls(status=CommandStatus.CANCELLED, text=text)
