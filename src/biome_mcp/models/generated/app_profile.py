# Generated from app-profile.data-contract
# source-sha256=e562a4f23539f9e88ec0b32dbffc7ac1ae9fd3a37e471a9b3630ddef6a0a48e7
# Edit the source, then run biome generate.

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class EnvAlias:
    var_name: str
    suffix: str


@dataclass(frozen=True, slots=True, kw_only=True)
class AppProfile:
    app_name: str
    protocol: str
    default_port: int
    default_host: str
    data_dir: str
    env_aliases: tuple[EnvAlias, ...]
