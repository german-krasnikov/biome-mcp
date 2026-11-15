"""Immutable value object for a resolved backend endpoint."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Source = Literal["flag", "env", "config", "port_file", "lock", "default"]


@dataclass(frozen=True, slots=True)
class ConnectionSpec:
    host: str
    port: int
    protocol: str
    app_name: str
    source: Source
    label: str | None = None
