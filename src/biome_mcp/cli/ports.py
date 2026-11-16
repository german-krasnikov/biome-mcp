"""Port file registry for multi-instance discovery."""
from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app_profile import AppProfile


def ports_dir(profile: AppProfile) -> Path:
    return profile.data_dir / "ports"


def write_port_file(port: int, pid: int, profile: AppProfile) -> Path:
    d = ports_dir(profile)
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{port}.port"
    p.write_text(str(pid), encoding="utf-8")
    return p


def remove_port_file(port: int, profile: AppProfile) -> None:
    p = ports_dir(profile) / f"{port}.port"
    p.unlink(missing_ok=True)


def iter_port_files(profile: AppProfile) -> Iterator[tuple[int, int | None]]:
    d = ports_dir(profile)
    if not d.exists():
        return
    for f in sorted(d.glob("*.port")):
        try:
            port_val = int(f.stem)
        except ValueError:
            continue
        pid = None
        with contextlib.suppress(OSError, ValueError):
            pid = int(f.read_text(encoding="utf-8").split("\n")[0].strip())
        yield port_val, pid
