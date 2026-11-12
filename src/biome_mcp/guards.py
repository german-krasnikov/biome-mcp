"""Guard protocol — pre-execution checks (engine adapters provide facts)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from biome_mcp.models.descriptor import CommandDescriptor


@dataclass(frozen=True)
class GuardResult:
    allowed: bool
    reason: str = ""

    @classmethod
    def allow(cls) -> GuardResult:
        return cls(allowed=True)

    @classmethod
    def deny(cls, reason: str) -> GuardResult:
        return cls(allowed=False, reason=reason)


class GuardProvider(Protocol):
    async def check(self, cmd: CommandDescriptor, args: dict[str, Any]) -> GuardResult: ...
