# Generated from dsl/decisions/error_class.logic
# source-sha256=19b8bddf09109092f7c5147c3a86e1015aad7831fa127ae058f04b7ef71099cc
# Edit the source, then run biome generate.

from __future__ import annotations

from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


class ErrorClassValues:
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ErrorClassInput:
    error_code: str


def error_class(inp: ErrorClassInput) -> str:
    _check("error.code", inp.error_code, "enum", values=(
        "connection_lost", "command_not_found", "invalid_arguments",
        "timeout", "permission_denied", "internal_error", "cancelled", "unknown",
    ))
    return _decide_error_class(inp)


__all__ = ["LogicInputError", "ErrorClassValues", "ErrorClassInput", "error_class"]


def _check(
    fact_id: str, value: object, kind: str, *,
    values: tuple[str, ...] = (),
) -> None:
    if kind == "enum":
        ok = isinstance(value, str) and value in values
    else:
        ok = isinstance(value, str)
    if not ok:
        raise LogicInputError(f"LOGIC_INPUT_CONTRACT: {fact_id}={value!r}")


def _decide_error_class(s: ErrorClassInput) -> str:
    # rule: connectionLost (priority 10)
    if s.error_code == "connection_lost":
        return "transient"
    # rule: timeout (priority 20)
    if s.error_code == "timeout":
        return "transient"
    # rule: invalidArgs (priority 30)
    if s.error_code == "invalid_arguments":
        return "permanent"
    # rule: permissionDenied (priority 40)
    if s.error_code == "permission_denied":
        return "permanent"
    # rule: commandNotFound (priority 50)
    if s.error_code == "command_not_found":
        return "permanent"
    return "unknown"
