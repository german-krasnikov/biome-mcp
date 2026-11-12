# Generated from dsl/decisions/batch_policy.logic
# source-sha256=295d15e0449532b2ed8f5bdea2e2031d5645ea7638021fa893e5ad32e6e17813
# Edit the source, then run biome generate.

from __future__ import annotations

from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


class BatchPolicyValues:
    CONTINUE = "continue"
    ROLLBACK = "rollback"
    STOP = "stop"


@dataclass(frozen=True, slots=True)
class BatchPolicyInput:
    cmd_effect: str
    error_class: str
    batch_supports_rollback: bool


def batch_policy(inp: BatchPolicyInput) -> str:
    _check("cmd.effect", inp.cmd_effect, "enum",
           values=("read", "write", "idempotent_write"))
    _check("error.class", inp.error_class, "enum",
           values=("transient", "permanent", "unknown"))
    _check("batch.supportsRollback", inp.batch_supports_rollback, "bool")
    return _decide_batch_policy(inp)


__all__ = [
    "LogicInputError", "BatchPolicyValues", "BatchPolicyInput", "batch_policy",
]


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


def _decide_batch_policy(s: BatchPolicyInput) -> str:
    # rule: readTransient (priority 10)
    if s.cmd_effect == "read" and s.error_class == "transient":
        return "continue"
    # rule: rollbackAvailable (priority 20)
    if (s.batch_supports_rollback is True) and (s.error_class == "permanent"):
        return "rollback"
    return "stop"
