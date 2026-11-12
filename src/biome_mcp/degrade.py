"""Graceful degradation ladder helper.

degrade(feature, steps, metrics=None) — runs steps until one returns truthy.
Zero overhead on success path. NO retry inside ladder.

metrics is injected (duck-typed: .inc(key, n=1) / .event(kind, **fields)),
never a module singleton — callers bind their own MetricsCollector instance
(or pass None to skip telemetry entirely).
"""
import inspect
import os
from collections.abc import Callable  # noqa: TC003
from typing import Any, Protocol

DEFAULT_DISABLED_ENV = "BIOME_MCP_DEGRADE_DISABLED"


class MetricsSink(Protocol):
    def inc(self, key: str, n: int = 1) -> None: ...
    def event(self, kind: str, **fields: Any) -> None: ...


async def degrade(
    feature: str,
    steps: list[tuple[str, Callable]],
    metrics: MetricsSink | None = None,
    disabled_env: str = DEFAULT_DISABLED_ENV,
) -> tuple[str, Any]:
    """Run steps until one returns truthy. Returns (step_name, value).

    Each step is (name, callable) returning value | None | coroutine. asyncio.Task not supported.
    First truthy result wins. If all fail → (last_step_name, None).

    Side effects on each failed step (skipped when metrics is None):
      metrics.inc('degraded.{feature}.{step}')
      metrics.event('degraded', feature=..., step=..., reason=...)
    On any ladder fall (at least one step failed before success or exhaustion):
      metrics.inc('degraded.{feature}')
    """
    disabled = os.environ.get(disabled_env) == "1"

    last_name = steps[-1][0] if steps else ""
    fell = False

    for name, fn in steps:
        reason = "none"
        if disabled:
            # No try/except — exceptions propagate raw; None still tries next rung
            result = fn()
            if inspect.iscoroutine(result):
                result = await result
        else:
            try:
                result = fn()
                if inspect.iscoroutine(result):
                    result = await result
            except Exception as e:
                result = None
                reason = f"raised:{type(e).__name__}"

        if result:
            if fell and metrics is not None:
                metrics.inc(f"degraded.{feature}")
            return (name, result)

        # Step returned None (or falsy)
        fell = True
        if metrics is not None:
            metrics.inc(f"degraded.{feature}.{name}")
            if not disabled:
                metrics.event("degraded", feature=feature, step=name, reason=reason)
        last_name = name

    # All steps exhausted
    if fell and metrics is not None:
        metrics.inc(f"degraded.{feature}")
    return (last_name, None)


def wrap_degraded(feature: str, step: str, value: Any | None) -> str:
    """Format degraded surface marker.

    value is None → '[DEGRADED:feature:step:no_fallback]'
    value is truthy → '[DEGRADED:feature:step]\\n<value>'
    """
    if value is None:
        return f"[DEGRADED:{feature}:{step}:no_fallback]"
    return f"[DEGRADED:{feature}:{step}]\n{value}"
