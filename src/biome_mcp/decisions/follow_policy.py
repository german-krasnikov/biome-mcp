# Generated from follow.logic
# source-sha256=b17b0228a2ec20caf99a457869a8f72c6571aad895a162ccaabf486ed2ca3d95
# Edit the source, then run biome generate.

from __future__ import annotations

import math
import typing as _typing
from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


@dataclass(frozen=True, slots=True)
class IsDoneInput:
    follow_max_polls: float
    follow_max_polls_present: bool
    follow_poll: float
    follow_result_status: str


def is_done(inp: IsDoneInput) -> bool:
    """Checks every input against the contract, then decides."""
    _check("follow.max_polls", inp.follow_max_polls, "number", lo=0, hi=10000,
            integer=True)
    _check("follow.max_polls_present", inp.follow_max_polls_present, "bool")
    _check("follow.poll", inp.follow_poll, "number", lo=0, hi=10000, integer=True)
    _check("follow.result_status", inp.follow_result_status, "enum", values=("pending",
            "done", "complete", "finished", "error",))
    return _decide_is_done(inp)


@dataclass(frozen=True, slots=True)
class IsFatalInput:
    follow_consecutive_errors: float
    follow_max_retries: float


def is_fatal(inp: IsFatalInput) -> bool:
    """Checks every input against the contract, then decides."""
    _check("follow.consecutive_errors", inp.follow_consecutive_errors, "number", lo=0,
            hi=10000, integer=True)
    _check("follow.max_retries", inp.follow_max_retries, "number", lo=0, hi=100,
            integer=True)
    return _decide_is_fatal(inp)


__all__ = ["LogicInputError", "IsDoneInput", "is_done", "IsFatalInput", "is_fatal"]


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


def _decide_is_done(s: IsDoneInput) -> bool:
    # rule: status (priority 10)
    if ((s.follow_result_status == "done") or (s.follow_result_status == "complete") or
            (s.follow_result_status == "finished")):
        return True
    return ((s.follow_max_polls_present is True) and (s.follow_poll >=
            s.follow_max_polls))


def _decide_is_fatal(s: IsFatalInput) -> bool:
    return s.follow_consecutive_errors > s.follow_max_retries
