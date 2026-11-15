"""Consumer-supplied application identity and defaults."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppProfile:
    app_name: str
    protocol: str = "tcp"
    default_port: int = 0
    default_host: str = "localhost"
    data_dir: Path = Path("")
    env_aliases: tuple[tuple[str, str], ...] = ()
    # Mapping (LEGACY_ENV_VAR, SUFFIX) checked before canonical BIOME_{APP}_SUFFIX.
    # Example: (("UNITY_MCP_PORT", "PORT"), ("UNITY_MCP_HOST", "HOST"))

    def __post_init__(self) -> None:
        if not self.app_name:
            msg = "app_name must not be empty"
            raise ValueError(msg)
        if self.data_dir != Path("") and not self.data_dir.is_absolute():
            msg = "data_dir must be an absolute path"
            raise ValueError(msg)
