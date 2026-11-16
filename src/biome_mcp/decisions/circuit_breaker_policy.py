# Generated from circuit-breaker.logic
# source-sha256=d5c27dbc32e200c573996cfd3794bf637e1c743efc662beb145fbe7e5260c402
# Edit the source, then run biome generate.

from __future__ import annotations

import math
import typing as _typing
from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


@dataclass(frozen=True, slots=True)
class IsOpenInput:
    circuit_breaker_state: str


def is_open(inp: IsOpenInput) -> bool:
    """Checks every input against the contract, then decides."""
    _check("circuitBreaker.state", inp.circuit_breaker_state, "enum", values=("closed",
            "open",))
    return _decide_is_open(inp)


@dataclass(frozen=True, slots=True)
class AllowRequestInput:
    circuit_breaker_cooldown_elapsed: bool
    circuit_breaker_state: str


def allow_request(inp: AllowRequestInput) -> bool:
    """Checks every input against the contract, then decides."""
    _check("circuitBreaker.cooldown_elapsed", inp.circuit_breaker_cooldown_elapsed,
            "bool")
    _check("circuitBreaker.state", inp.circuit_breaker_state, "enum", values=("closed",
            "open",))
    return _decide_allow_request(inp)


@dataclass(frozen=True, slots=True)
class ShouldOpenInput:
    circuit_breaker_failures: float
    circuit_breaker_threshold: float


def should_open(inp: ShouldOpenInput) -> bool:
    """Checks every input against the contract, then decides."""
    _check("circuitBreaker.failures", inp.circuit_breaker_failures, "number", lo=0,
            hi=999, integer=True)
    _check("circuitBreaker.threshold", inp.circuit_breaker_threshold, "number", lo=1,
            hi=100, integer=True)
    return _decide_should_open(inp)


__all__ = [
    "LogicInputError",
    "IsOpenInput",
    "is_open",
    "AllowRequestInput",
    "allow_request",
    "ShouldOpenInput",
    "should_open",
]


# Unchecked evaluators: reachable only through the checked functions above.
def _check(
    fact_id: str,
    value: object,
    kind: str,
    lo: float | None = None,
    hi: float | None = None,
    integer: bool = False,
    values: tuple[str, ...] = (),
) -> None:
    if kind == "bool":
        ok = isinstance(value, bool)
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
    elif kind == "enum":
        ok = isinstance(value, str) and value in values
    else:
        ok = isinstance(value, str)
    if not ok:
        raise LogicInputError(f"LOGIC_INPUT_CONTRACT: {fact_id}={value!r}")


def _decide_is_open(s: IsOpenInput | AllowRequestInput) -> bool:
    return s.circuit_breaker_state == "open"


def _decide_allow_request(s: AllowRequestInput) -> bool:
    # rule: closed (priority 10)
    if s.circuit_breaker_state == "closed":
        return True
    return ((s.circuit_breaker_state == "open") and (s.circuit_breaker_cooldown_elapsed
            is True))


def _decide_should_open(s: ShouldOpenInput) -> bool:
    return s.circuit_breaker_failures >= s.circuit_breaker_threshold
