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


def write_port_file(port: int, pid: int, profile: AppProfile,
                    project_path: str | None = None) -> Path:
    d = ports_dir(profile)
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{port}.port"
    content = f"{pid}\n{project_path}" if project_path is not None else str(pid)
    p.write_text(content, encoding="utf-8")
    return p


def remove_port_file(port: int, profile: AppProfile) -> None:
    p = ports_dir(profile) / f"{port}.port"
    p.unlink(missing_ok=True)


def iter_port_files(profile: AppProfile) -> Iterator[tuple[int, int | None, str | None]]:
    d = ports_dir(profile)
    if not d.exists():
        return
    for f in sorted(d.glob("*.port")):
        try:
            port_val = int(f.stem)
        except ValueError:
            continue
        pid = None
        project_path = None
        with contextlib.suppress(OSError, ValueError):
            lines = f.read_text(encoding="utf-8").split("\n")
            pid = int(lines[0].strip())
            if len(lines) > 1 and lines[1].strip():
                project_path = lines[1].strip()
        yield port_val, pid, project_path
