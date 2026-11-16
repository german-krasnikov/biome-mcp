"""Generate surfaces/__init__.py from dsl/surfaces/*.module-surface files."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from .surface_reader import load_surface


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _const_name(stem: str) -> str:
    return stem.replace("-", "_").upper() + "_SURFACE"


def generate(surfaces_dir: Path, out_path: Path) -> str:
    files = sorted(surfaces_dir.glob("*.module-surface"))
    lines = ['"""Generated module surfaces — DO NOT EDIT."""']
    for f in files:
        lines.append(f"# {f.stem}-sha256={_sha(f)}")
    lines.append("")
    for f in files:
        surface = load_surface(f)
        items = sorted(surface.exports)
        lines.append(f"{_const_name(f.stem)}: frozenset[str] = frozenset({{")
        for e in items:
            lines.append(f'    "{e}",')
        lines.append("})")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    repo = Path(__file__).resolve().parents[3]
    surfaces_dir = repo / "dsl" / "surfaces"
    out_path = repo / "src" / "biome_mcp" / "surfaces" / "__init__.py"
    content = generate(surfaces_dir, out_path)
    if "--check" in sys.argv:
        if not out_path.exists() or out_path.read_text(encoding="utf-8") != content:
            print(f"stale: {out_path.relative_to(repo)}", file=sys.stderr)
            sys.exit(1)
        print("surfaces up to date")
        sys.exit(0)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(f"wrote {out_path.relative_to(repo)}")


if __name__ == "__main__":
    main()
