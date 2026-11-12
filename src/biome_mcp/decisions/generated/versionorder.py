# Generated from dsl/decisions/versionorder.logic
# source-sha256=2ff49c8d1131a8319ab430d7a9c351414d47cc87e9fd5a5bb09c668423840c86
# Edit the source, then run biome generate.

from __future__ import annotations

from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


@dataclass(frozen=True, slots=True)
class IsNewerInput:
    ver_cand_pre: bool
    ver_cur_pre: bool
    ver_parsed: bool
    ver_triple: str


def is_newer(inp: IsNewerInput) -> bool:
    _check("ver.candPre", inp.ver_cand_pre, "bool")
    _check("ver.curPre", inp.ver_cur_pre, "bool")
    _check("ver.parsed", inp.ver_parsed, "bool")
    _check("ver.triple", inp.ver_triple, "enum",
           values=("less", "equal", "greater"))
    return _decide_is_newer(inp)


__all__ = ["LogicInputError", "IsNewerInput", "is_newer"]


def _check(
    fact_id: str, value: object, kind: str, *,
    values: tuple[str, ...] = (),
) -> None:
    if kind == "bool":
        ok = isinstance(value, bool)
    elif kind == "enum":
        ok = isinstance(value, str) and value in values
    else:
        ok = isinstance(value, str)
    if not ok:
        raise LogicInputError(f"LOGIC_INPUT_CONTRACT: {fact_id}={value!r}")


def _decide_is_newer(s: IsNewerInput) -> bool:
    # rule: unparsed (priority 5)
    if s.ver_parsed is not True:
        return False
    # rule: stableUserNeverSeesRc (priority 10)
    if (s.ver_cand_pre is True) and (s.ver_cur_pre is not True):
        return False
    # rule: higher (priority 20)
    if s.ver_triple == "greater":
        return True
    # rule: releaseOverItsRc (priority 30)
    return (
        (s.ver_triple == "equal")
        and (s.ver_cur_pre is True)
        and (s.ver_cand_pre is not True)
    )
