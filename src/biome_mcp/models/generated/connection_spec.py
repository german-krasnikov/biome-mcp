# Generated from connection-spec.data-contract
# source-sha256=cc52960530fc469c371b7585f7188b2558f1d0d18a301ba7c1b2a10eba0348d7
# Edit the source, then run biome generate.

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionSpec:
    host: str
    port: float
    protocol: str
    app_name: str
    source: str
    label: str | None
