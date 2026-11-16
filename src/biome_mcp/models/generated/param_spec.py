# Generated from param-spec.data-contract
# source-sha256=72fcd0053b0a324864e36872329274f8ebc7510d00da20a106b99f014f5b7b2b
# Edit the source, then run biome generate.

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True, kw_only=True)
class ParamSpec:
    name: str
    param_type: str
    required: bool
    default: Any | None
    description: str
