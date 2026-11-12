"""Command registry — descriptor metadata store.

Handlers live in FastMCP (@mcp.tool). This registry holds engine-agnostic
CommandDescriptor metadata for guards, batch policy, and rendering.
"""

from __future__ import annotations

from biome_mcp.errors import BiomeError, ErrorCode
from biome_mcp.models.descriptor import CommandDescriptor


class Registry:
    def __init__(self) -> None:
        self._descriptors: dict[str, CommandDescriptor] = {}

    def register(self, descriptor: CommandDescriptor) -> None:
        if descriptor.name in self._descriptors:
            raise BiomeError(
                ErrorCode.INVALID_ARGUMENTS,
                f"command {descriptor.name!r} already registered",
            )
        self._descriptors[descriptor.name] = descriptor

    def get(self, name: str) -> CommandDescriptor:
        try:
            return self._descriptors[name]
        except KeyError:
            raise BiomeError(
                ErrorCode.COMMAND_NOT_FOUND, f"unknown command {name!r}"
            ) from None

    def names(self, namespace: str | None = None) -> tuple[str, ...]:
        if namespace is None:
            return tuple(sorted(self._descriptors))
        prefix = f"{namespace}."
        return tuple(sorted(n for n in self._descriptors if n.startswith(prefix)))

    def descriptors(self) -> tuple[CommandDescriptor, ...]:
        return tuple(self._descriptors.values())
