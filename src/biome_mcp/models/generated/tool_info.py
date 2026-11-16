# Generated from tool-info.data-contract
# source-sha256=d801784696aa17cf8f80c30143044dd8173e918aefa3eb6d5bd466cd52bf7dff
# Edit the source, then run biome generate.

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolInfo:
    name: str
    description: str
    input_schema: Any
    effect: str | None
    namespace: str | None
