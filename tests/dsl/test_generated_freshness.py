"""Verify generated files are fresh — sha256 in header matches DSL source (P16)."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DECISIONS_DIR = REPO / "src" / "biome_mcp" / "decisions"
GENERATED_DIR = REPO / "src" / "biome_mcp" / "models" / "generated"

SHA_RE = re.compile(r"source-sha256=([0-9a-f]{64})")


def _extract_sha(generated: Path) -> str | None:
    text = generated.read_text(encoding="utf-8")
    m = SHA_RE.search(text)
    return m.group(1) if m else None


def _source_sha(source: Path) -> str:
    return hashlib.sha256(source.read_bytes()).hexdigest()


LOGIC_PAIRS = [
    ("dsl/services/circuit-breaker.logic", "decisions/circuit_breaker_policy.py"),
    ("dsl/follow/follow.logic", "decisions/follow_policy.py"),
    ("dsl/services/tcp-session.logic", "decisions/tcp_session_policy.py"),
    ("dsl/services/resolver.logic", "decisions/resolver_policy.py"),
]


@pytest.mark.parametrize("source_rel,gen_rel", LOGIC_PAIRS, ids=[p[0] for p in LOGIC_PAIRS])
def test_logic_generated_fresh(source_rel: str, gen_rel: str) -> None:
    source = REPO / source_rel
    generated = REPO / "src" / "biome_mcp" / gen_rel
    assert source.exists(), f"DSL source missing: {source_rel}"
    assert generated.exists(), f"Generated file missing: {gen_rel}"
    embedded = _extract_sha(generated)
    assert embedded is not None, f"No source-sha256 in {gen_rel}"
    actual = _source_sha(source)
    assert embedded == actual, (
        f"Stale generated file {gen_rel}: "
        f"embedded sha256={embedded[:12]}…, source sha256={actual[:12]}…. "
        f"Regenerate with: biome logic generate --source {source_rel}"
    )


def test_generated_models_exist() -> None:
    py_files = list(GENERATED_DIR.glob("*.py"))
    non_init = [f for f in py_files if f.name != "__init__.py"]
    assert len(non_init) >= 10, f"Expected ≥10 generated model files, got {len(non_init)}"
