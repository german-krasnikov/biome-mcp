"""Per-app persistent CLI config. Never raises on load."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AppConfig:
    host: str = "localhost"
    port: int = 0

    @classmethod
    def load(cls, config_path: Path) -> AppConfig:
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            return cls(
                host=str(data.get("host", "localhost")) or "localhost",
                port=int(data.get("port", 0)),
            )
        except (OSError, json.JSONDecodeError, TypeError, AttributeError, ValueError):
            return cls()

    def save(self, config_path: Path) -> None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = config_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        os.replace(tmp, config_path)
