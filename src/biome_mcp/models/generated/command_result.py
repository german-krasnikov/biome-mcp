# Generated from command-result.data-contract
# source-sha256=f68a4426287920b39f23e08f23f3f0ba7089fd307ea1b3fac4222a11ae4fa6aa
# Edit the source, then run biome generate.

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


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandResult:
    status: CommandStatus
    text: str
    data: Any | None
    complete: bool
    error_code: str | None
