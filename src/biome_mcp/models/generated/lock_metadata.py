# Generated from lock-metadata.data-contract
# source-sha256=2c4388c2e2ac0cbd1464a5949cba3237a1e635b331cd42e2dd7a8b5ec5053fb7
# Edit the source, then run biome generate.

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class LockMetadata:
    ppid: int
