"""Resolve connection from priority chain: flag → env → config → port_file → default."""
from __future__ import annotations

import os
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


def _is_path_prefix(cwd: str, prefix: str) -> bool:
    """True if prefix is a parent of (or equal to) cwd. Handles Windows normcase."""
    cwd_n = os.path.normcase(os.path.normpath(cwd))
    pre_n = os.path.normcase(os.path.normpath(prefix))
    sep = os.path.normcase(os.sep)
    return cwd_n == pre_n or cwd_n.startswith(pre_n + sep)


class ConnectionResolver:
    def __init__(self, profile: AppProfile) -> None:
        self._profile = profile

    def resolve(
        self,
        cli_port: int | None = None,
        cli_host: str | None = None,
        project_path: str | None = None,
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

        port_file_spec = self._resolve_port_file(p, project_path)
        if port_file_spec is not None:
            return port_file_spec

        for entry in list_servers(p.data_dir / "locks"):
            return self._spec(p.default_host, entry["port"], "lock")

        return self._spec(p.default_host, p.default_port, "default")

    def _resolve_port_file(self, p: AppProfile, project_path: str | None) -> ConnectionSpec | None:
        candidates = [
            (port_val, pid, pp)
            for port_val, pid, pp in iter_port_files(p)
            if pid is None or is_pid_alive(pid)
        ]
        if not candidates:
            return None

        if project_path:
            # Prefer longest-matching prefix (most specific project path)
            matches = [
                (len(os.path.normpath(pp)), port_val)
                for port_val, pid, pp in candidates
                if pp and _is_path_prefix(project_path, pp)
            ]
            if matches:
                matches.sort(reverse=True)
                _, port_val = matches[0]
                return self._spec(p.default_host, port_val, "port_file")

        # Fall back to first alphabetically alive (sorted by iter_port_files)
        port_val, _, _ = candidates[0]
        return self._spec(p.default_host, port_val, "port_file")

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
