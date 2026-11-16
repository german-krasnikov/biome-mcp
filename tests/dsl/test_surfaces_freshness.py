"""Verify module surface declarations are fresh and symbols exist (P7/P16)."""
from __future__ import annotations

import hashlib
import importlib
import re
from pathlib import Path

import pytest

from biome_mcp.dsl.surface_reader import load_surface

REPO = Path(__file__).resolve().parents[2]
SURFACES_DIR = REPO / "dsl" / "surfaces"
GENERATED = REPO / "src" / "biome_mcp" / "surfaces" / "__init__.py"

SHA_RE = re.compile(r"(\w+)-sha256=([0-9a-f]{64})")
SURFACE_FILES = sorted(SURFACES_DIR.glob("*.module-surface"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _embedded_shas() -> dict[str, str]:
    text = GENERATED.read_text(encoding="utf-8")
    return {m.group(1): m.group(2) for m in SHA_RE.finditer(text)}


@pytest.mark.parametrize("sf", SURFACE_FILES, ids=[f.stem for f in SURFACE_FILES])
def test_surface_fresh(sf: Path) -> None:
    shas = _embedded_shas()
    assert sf.stem in shas, f"No sha256 for {sf.stem} in surfaces/__init__.py"
    assert shas[sf.stem] == _sha(sf), (
        f"Stale surface for {sf.stem}. Regenerate: python -m biome_mcp.dsl.surface_gen"
    )


@pytest.mark.parametrize("sf", SURFACE_FILES, ids=[f.stem for f in SURFACE_FILES])
def test_declared_symbols_exist(sf: Path) -> None:
    surface = load_surface(sf)
    mod = importlib.import_module(surface.module)
    for name in surface.exports:
        assert hasattr(mod, name), f"{surface.module} missing declared EXPORT '{name}'"
