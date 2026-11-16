"""Parse .module-surface files — public API declarations for package boundaries."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ModuleSurface:
    module: str
    bridge: str | None = None
    exports: list[str] = field(default_factory=list)


def parse_surface(source: str) -> ModuleSurface:
    module = bridge = None
    exports: list[str] = []
    for lineno, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("MODULE "):
            module = line.split(None, 1)[1]
        elif line.startswith("BRIDGE "):
            bridge = line.split(None, 1)[1]
        elif line.startswith("EXPORT "):
            name = line.split(None, 1)[1]
            if name.startswith("_"):
                msg = f"line {lineno}: EXPORT of private name '{name}'"
                raise SyntaxError(msg)
            exports.append(name)
        else:
            msg = f"line {lineno}: unknown keyword '{line.split()[0]}'"
            raise SyntaxError(msg)
    if module is None:
        raise SyntaxError("MODULE is required")
    return ModuleSurface(module=module, bridge=bridge, exports=exports)


def load_surface(path: Path) -> ModuleSurface:
    return parse_surface(path.read_text(encoding="utf-8"))
