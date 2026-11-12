"""Engine-agnostic error codes and base exception."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    CONNECTION_LOST = "connection_lost"
    COMMAND_NOT_FOUND = "command_not_found"
    INVALID_ARGUMENTS = "invalid_arguments"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    INTERNAL_ERROR = "internal_error"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class BiomeError(Exception):
    def __init__(
        self, code: str, message: str, *, details: Mapping[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
