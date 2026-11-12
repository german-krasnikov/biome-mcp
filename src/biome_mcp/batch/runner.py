"""Sequential batch runner — execute parsed commands with policy on errors."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from biome_mcp.batch.model import BatchDocument
from biome_mcp.decisions.generated.batch_policy import BatchPolicyInput, batch_policy
from biome_mcp.decisions.generated.error_class import ErrorClassInput, error_class
from biome_mcp.errors import BiomeError
from biome_mcp.models.result import CommandResult, CommandStatus
from biome_mcp.registry import Registry

Handler = Callable[[str, dict[str, Any]], Awaitable[CommandResult]]


@dataclass(frozen=True)
class StepResult:
    step_id: str
    name: str
    result: CommandResult


async def run_batch(
    registry: Registry,
    doc: BatchDocument,
    handler: Handler,
    *,
    supports_rollback: bool = False,
) -> list[StepResult]:
    results: list[StepResult] = []
    for cmd in doc.commands:
        args = {a.key: a.value for a in cmd.args}
        try:
            result = await handler(cmd.name, args)
        except BiomeError as exc:
            result = CommandResult.error(exc.code, exc.message)
        results.append(StepResult(step_id=cmd.step_id, name=cmd.name, result=result))
        if result.status != CommandStatus.OK:
            try:
                desc = registry.get(cmd.name)
                effect = desc.effect.value
            except Exception:
                effect = "write"
            policy = _decide_policy(result, effect, supports_rollback)
            if policy != "continue":
                break
    return results


def _decide_policy(
    result: CommandResult, effect: str, supports_rollback: bool,
) -> str:
    err_class = "unknown"
    if result.error_code:
        err_class = error_class(ErrorClassInput(error_code=result.error_code))
    return batch_policy(BatchPolicyInput(
        cmd_effect=effect,
        error_class=err_class,
        batch_supports_rollback=supports_rollback,
    ))
