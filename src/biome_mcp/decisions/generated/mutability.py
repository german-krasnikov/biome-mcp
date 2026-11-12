# Generated from dsl/decisions/mutability.logic
# source-sha256=2b7a9bc5862c5a4e0ea7b11099dc98a2455f1f565e05a23347f6d7160aa07e0e
# Edit the source, then run biome generate.

from __future__ import annotations

from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


@dataclass(frozen=True, slots=True)
class IsMutatingInput:
    cmd_effect: str


def is_mutating(inp: IsMutatingInput) -> bool:
    _check("cmd.effect", inp.cmd_effect, "enum",
           values=("read", "write", "idempotent_write"))
    return _decide_is_mutating(inp)


__all__ = ["LogicInputError", "IsMutatingInput", "is_mutating"]


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


def _decide_is_mutating(s: IsMutatingInput) -> bool:
    # rule: readEffect (priority 10)
    if s.cmd_effect == "read":
        return False
    return True
