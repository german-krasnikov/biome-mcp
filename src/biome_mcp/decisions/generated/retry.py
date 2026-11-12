# Generated from dsl/decisions/retry.logic
# source-sha256=6a71caf58068cd5540accd118a672a0e7209be17e2ff3eb07f3b7a9c596e2b14
# Edit the source, then run biome generate.

from __future__ import annotations

import math
import typing as _typing
from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


class RetryGateValues:
    FAIL = "fail"
    MAX_RETRIES = "max_retries"
    RETRY = "retry"


@dataclass(frozen=True, slots=True)
class RetryGateInput:
    retry_error_code: str
    retry_attempt: float
    retry_max_retries: float


def retry_gate(inp: RetryGateInput) -> str:
    _check("retry.errorCode", inp.retry_error_code, "enum", values=(
        "connection_lost", "timeout", "cancelled", "invalid_arguments",
        "permission_denied", "command_not_found", "internal_error", "unknown",
    ))
    _check("retry.attempt", inp.retry_attempt, "number", lo=0, hi=1000000,
           integer=True)
    _check("retry.maxRetries", inp.retry_max_retries, "number", lo=0, hi=1000000,
           integer=True)
    return _decide_retry_gate(inp)


__all__ = ["LogicInputError", "RetryGateValues", "RetryGateInput", "retry_gate"]


def _check(
    fact_id: str, value: object, kind: str, *,
    lo: float | None = None, hi: float | None = None,
    integer: bool = False, values: tuple[str, ...] = (),
) -> None:
    if kind == "enum":
        ok = isinstance(value, str) and value in values
    elif kind == "number":
        ok = (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
        number = _typing.cast("float", value)
        ok = ok and (lo is None or number >= lo) and (hi is None or number <= hi)
        if integer:
            ok = ok and float(number).is_integer() and abs(number) <= 9007199254740991
    else:
        ok = isinstance(value, str)
    if not ok:
        raise LogicInputError(f"LOGIC_INPUT_CONTRACT: {fact_id}={value!r}")


def _decide_retry_gate(s: RetryGateInput) -> str:
    # rule: maxRetries (priority 5)
    if s.retry_attempt >= s.retry_max_retries:
        return "max_retries"
    # rule: connectionLost (priority 10)
    if s.retry_error_code == "connection_lost":
        return "retry"
    # rule: timeout (priority 20)
    if s.retry_error_code == "timeout":
        return "retry"
    # rule: cancelled (priority 30)
    if s.retry_error_code == "cancelled":
        return "fail"
    # rule: invalidArgs (priority 40)
    if s.retry_error_code == "invalid_arguments":
        return "fail"
    # rule: permissionDenied (priority 50)
    if s.retry_error_code == "permission_denied":
        return "fail"
    # rule: commandNotFound (priority 60)
    if s.retry_error_code == "command_not_found":
        return "fail"
    return "fail"
