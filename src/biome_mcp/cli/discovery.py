"""Find running instances by merging lockfiles and port files."""
from __future__ import annotations

from typing import TYPE_CHECKING

from biome_mcp.server_control import is_pid_alive, list_servers

from .connection import ConnectionSpec
from .ports import iter_port_files

if TYPE_CHECKING:
    from .app_profile import AppProfile


def discover_instances(profile: AppProfile) -> list[ConnectionSpec]:
    seen: dict[int, ConnectionSpec] = {}

    lock_dir = profile.data_dir / "locks"
    for entry in list_servers(lock_dir):
        port = entry["port"]
        seen[port] = ConnectionSpec(
            host=profile.default_host,
            port=port,
            protocol=profile.protocol,
            app_name=profile.app_name,
            source="lock",
            label=f"pid={entry['pid']}",
        )

    for port, pid in iter_port_files(profile):
        if port in seen:
            continue
        if pid is not None and not is_pid_alive(pid):
            continue
        seen[port] = ConnectionSpec(
            host=profile.default_host,
            port=port,
            protocol=profile.protocol,
            app_name=profile.app_name,
            source="port_file",
            label=f"pid={pid}" if pid else None,
        )

    return sorted(seen.values(), key=lambda s: s.port)
