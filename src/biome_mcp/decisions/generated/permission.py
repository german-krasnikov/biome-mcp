# Generated from dsl/decisions/permission.logic
# source-sha256=9fb7f767f75e07216a172c029021a16ebc94e8814710878d1f0f098208e63031
# Edit the source, then run biome generate.

from __future__ import annotations

from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


class RequiredPermissionValues:
    READ = "read"
    WRITE = "write"


@dataclass(frozen=True, slots=True)
class RequiredPermissionInput:
    cmd_effect: str


def required_permission(inp: RequiredPermissionInput) -> str:
    _check("cmd.effect", inp.cmd_effect, "enum",
           values=("read", "write", "idempotent_write"))
    return _decide_required_permission(inp)


__all__ = [
    "LogicInputError", "RequiredPermissionValues",
    "RequiredPermissionInput", "required_permission",
]


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


def _decide_required_permission(s: RequiredPermissionInput) -> str:
    # rule: readEffect (priority 10)
    if s.cmd_effect == "read":
        return "read"
    # rule: writeEffect (priority 20)
    if s.cmd_effect == "write":
        return "write"
    # rule: idempotentEffect (priority 25)
    if s.cmd_effect == "idempotent_write":
        return "write"
    return "write"
