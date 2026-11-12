"""Executor — unified validate → guard → execute pipeline.

Handlers live in FastMCP. Executor provides the guard chain, validation,
and policy layer that wraps around any handler invocation.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from biome_mcp.errors import BiomeError, ErrorCode
from biome_mcp.guards import GuardProvider
from biome_mcp.models.descriptor import CommandDescriptor
from biome_mcp.models.result import CommandResult, CommandStatus
from biome_mcp.registry import Registry

Handler = Callable[[dict[str, Any]], Awaitable[CommandResult]]


class Executor:
    def __init__(
        self,
        registry: Registry,
        guards: Sequence[GuardProvider] = (),
    ) -> None:
        self._registry = registry
        self._guards = list(guards)

    def get_descriptor(self, name: str) -> CommandDescriptor:
        return self._registry.get(name)

    async def execute(
        self, name: str, args: dict[str, Any], handler: Handler,
    ) -> CommandResult:
        try:
            descriptor = self._registry.get(name)
        except BiomeError as exc:
            return CommandResult.error(exc.code, exc.message)
        validation = _validate_args(descriptor, args)
        if validation is not None:
            return validation
        for guard in self._guards:
            result = await guard.check(descriptor, args)
            if not result.allowed:
                return CommandResult(
                    status=CommandStatus.CANCELLED,
                    text=result.reason or "blocked by guard",
                )
        try:
            return await handler(args)
        except BiomeError as exc:
            return CommandResult.error(exc.code, exc.message)

    async def execute_batch(
        self,
        commands: Sequence[tuple[str, dict[str, Any], Handler]],
    ) -> list[CommandResult]:
        results: list[CommandResult] = []
        for name, args, handler in commands:
            result = await self.execute(name, args, handler)
            results.append(result)
            if result.status != CommandStatus.OK:
                break
        return results


def _validate_args(
    descriptor: CommandDescriptor, args: dict[str, Any],
) -> CommandResult | None:
    for param in descriptor.params:
        if param.required and param.name not in args:
            return CommandResult.error(
                ErrorCode.INVALID_ARGUMENTS,
                f"missing required parameter: {param.name}",
            )
    return None
