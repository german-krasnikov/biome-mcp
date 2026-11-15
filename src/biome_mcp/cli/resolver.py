"""Resolve connection from priority chain: flag → env → config → port_file → default."""
from __future__ import annotations

from typing import TYPE_CHECKING

from biome_mcp.server_control import is_pid_alive, list_servers

from ._constants import CLI_CONFIG_FILENAME
from .app_config import AppConfig
from .connection import ConnectionSpec
from .discovery import discover_instances
from .env_vars import env_host, env_port
from .ports import iter_port_files

if TYPE_CHECKING:
    from .app_profile import AppProfile


class ConnectionResolver:
    def __init__(self, profile: AppProfile) -> None:
        self._profile = profile

    def resolve(
        self,
        cli_port: int | None = None,
        cli_host: str | None = None,
    ) -> ConnectionSpec:
        p = self._profile

        if cli_port is not None:
            return self._spec(cli_host or p.default_host, cli_port, "flag")

        ep = env_port(p.app_name, p.env_aliases)
        if ep is not None:
            return self._spec(env_host(p.app_name, p.env_aliases) or p.default_host, ep, "env")

        cfg = AppConfig.load(p.data_dir / CLI_CONFIG_FILENAME)
        if cfg.port:
            return self._spec(cfg.host, cfg.port, "config")

        for port_val, pid in iter_port_files(p):
            if pid is None or is_pid_alive(pid):
                return self._spec(p.default_host, port_val, "port_file")

        for entry in list_servers(p.data_dir / "locks"):
            return self._spec(p.default_host, entry["port"], "lock")

        return self._spec(p.default_host, p.default_port, "default")

    def resolve_all(self) -> list[ConnectionSpec]:
        return discover_instances(self._profile)

    def _spec(self, host: str, port: int, source: str) -> ConnectionSpec:
        return ConnectionSpec(
            host=host,
            port=port,
            protocol=self._profile.protocol,
            app_name=self._profile.app_name,
            source=source,
        )
