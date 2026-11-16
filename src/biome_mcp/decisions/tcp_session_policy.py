# Generated from tcp-session.logic
# source-sha256=57237101ef4abf5388ddf95fb9f577a6da1de941dfe2f32fffed55fc5257382a
# Edit the source, then run biome generate.

from __future__ import annotations

import math
import typing as _typing
from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


@dataclass(frozen=True, slots=True)
class IsConnectedInput:
    tcp_session_reader_present: bool
    tcp_session_writer_present: bool


def is_connected(inp: IsConnectedInput) -> bool:
    """Checks every input against the contract, then decides."""
    _check("tcpSession.reader_present", inp.tcp_session_reader_present, "bool")
    _check("tcpSession.writer_present", inp.tcp_session_writer_present, "bool")
    return _decide_is_connected(inp)


__all__ = ["LogicInputError", "IsConnectedInput", "is_connected"]


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


def _decide_is_connected(s: IsConnectedInput) -> bool:
    return ((s.tcp_session_reader_present is True) and (s.tcp_session_writer_present is
            True))
