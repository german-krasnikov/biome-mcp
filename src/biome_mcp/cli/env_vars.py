"""Resolve connection params from environment variables."""
from __future__ import annotations

import os


def env_key(app_name: str, suffix: str) -> str:
    """Build env var name: 'unity-biome-mcp' + 'PORT' → 'BIOME_UNITY_BIOME_MCP_PORT'."""
    normalized = app_name.upper().replace("-", "_")
    return f"BIOME_{normalized}_{suffix}"


def env_port(app_name: str, aliases: tuple[tuple[str, str], ...] = ()) -> int | None:
    for var, suffix in aliases:
        if suffix == "PORT":
            raw = os.environ.get(var)
            if raw is not None:
                try:
                    return int(raw)
                except ValueError:
                    pass
    raw = os.environ.get(env_key(app_name, "PORT"))
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def env_host(app_name: str, aliases: tuple[tuple[str, str], ...] = ()) -> str | None:
    for var, suffix in aliases:
        if suffix == "HOST":
            val = os.environ.get(var)
            if val:
                return val
    return os.environ.get(env_key(app_name, "HOST")) or None
