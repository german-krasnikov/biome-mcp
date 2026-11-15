"""FollowPolicy — extension points for --follow mode."""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from biome_mcp.models.result import CommandResult


def _default_is_done(result: "CommandResult") -> bool:
    """True when result.text is JSON with status in {"done","complete","finished"}.

    Terminal statuses: see dsl/follow/completion.examples
    """
    text = (result.text or "").strip()
    if not text.startswith("{"):
        return False
    try:
        data = json.loads(text)
        return data.get("status") in ("done", "complete", "finished")
    except (json.JSONDecodeError, AttributeError):
        return False


@dataclass
class FollowPolicy:  # dsl/models/follow-policy.data-contract
    # Completion detection — override for non-JSON protocols
    is_done: Callable[["CommandResult"], bool] = field(default=_default_is_done)

    # Output format — None = default JSON-lines. Signature: (poll, result, is_final) -> str
    format_line: Callable[[int, "CommandResult", bool], str] | None = None

    # Clamp user-supplied interval to [min, max] seconds
    interval_bounds: tuple[float, float] = (0.0, 3600.0)

    # Suppress up to N consecutive transient errors before exiting 1
    max_retries: int = 0

    # Per-poll asyncio.wait_for timeout (None = no timeout)
    poll_timeout: float | None = None
