"""CommandDescriptor — engine-agnostic tool contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class CommandEffect(StrEnum):
    READ = "read"
    WRITE = "write"
    IDEMPOTENT_WRITE = "idempotent_write"


@dataclass(frozen=True)
class ParamSpec:
    name: str
    param_type: type
    required: bool = True
    default: Any = None
    description: str = ""


@dataclass(frozen=True)
class CommandDescriptor:
    name: str
    namespace: str
    summary: str
    params: tuple[ParamSpec, ...]
    effect: CommandEffect = CommandEffect.READ
    batchable: bool = True
    requires: frozenset[str] = frozenset()
    blast_radius: int = 0
