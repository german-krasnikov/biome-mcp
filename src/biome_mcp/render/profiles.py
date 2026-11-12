"""Configurable compress profiles for rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderProfile:
    name: str
    max_chars: int
    include_data: bool = True
    include_status: bool = True
    truncation_suffix: str = " [truncated]"


DEFAULT = RenderProfile(name="default", max_chars=4096)
COMPACT = RenderProfile(name="compact", max_chars=1024, include_data=False)
VERBOSE = RenderProfile(name="verbose", max_chars=16384)

PROFILES: dict[str, RenderProfile] = {
    p.name: p for p in (DEFAULT, COMPACT, VERBOSE)
}
