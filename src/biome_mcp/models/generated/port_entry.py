# Generated from port-entry.data-contract
# source-sha256=463752869e859d9f06e2ee4317545c9a5081c8090d93e966fe8c32a30f71f714
# Edit the source, then run biome generate.

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class PortEntry:
    port: int
    pid: int | None
    project_path: str | None
