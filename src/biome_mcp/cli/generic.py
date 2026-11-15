"""Core CLI utilities — engine-agnostic. No mcp imports.

Handlers live in handlers.py; this module owns parse_kv, exit_code_for,
and re-exports handlers so existing imports keep working.
"""
from __future__ import annotations

from typing import Any

from biome_mcp.errors import BiomeError

from ._constants import BUILTIN_DESCS as _BUILTIN_DESCS  # noqa: F401
from ._constants import BUILTIN_USAGE as _BUILTIN_USAGE  # noqa: F401
from ._constants import EXIT_MAP  # noqa: F401
from ._constants import TOOL_HINT_THRESHOLD as _TOOL_HINT_THRESHOLD  # noqa: F401
from .handlers import (  # noqa: F401
    make_batch_handler,
    make_call_handler,
    make_describe_handler,
    make_help_handler,
    make_list_handler,
)


def parse_kv(tokens: list[str]) -> dict[str, Any]:
    """Parse ["key=value", ...] with type coercion."""
    result: dict[str, Any] = {}
    for token in tokens:
        if "=" not in token:
            raise ValueError(f"expected key=value, got {token!r}")
        key, _, raw = token.partition("=")
        result[key] = _coerce(raw)
    return result


def _coerce(val: str) -> Any:
    lower = val.lower()
    if lower in ("true", "yes"):
        return True
    if lower in ("false", "no"):
        return False
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def exit_code_for(err: BiomeError | None) -> int:
    """Map BiomeError to POSIX exit code."""
    if err is None:
        return 0
    return EXIT_MAP.get(str(err.code), 1)
