"""Engine-agnostic error codes and base exception."""

from __future__ import annotations

from enum import StrEnum


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
    def __init__(self, code: ErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")
