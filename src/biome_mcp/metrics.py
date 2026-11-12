"""Counters + timers for command execution tracking."""

from __future__ import annotations

import functools
import inspect
import json
import os
import statistics
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

OBSERVATION_WINDOW = 256
DEFAULT_SINK_ENV_VAR = "BIOME_MCP_METRICS_SINK"

F = TypeVar("F", bound=Callable[..., Any])


def p95(seq) -> float:
    """95th percentile. Falls back to max() below 20 samples — too few for a
    stable tail estimate, so the worst observed value is the honest answer."""
    vals = list(seq)
    if not vals:
        return 0.0
    if len(vals) < 20:
        return max(vals)
    s = sorted(vals)
    idx = int(0.95 * len(s))
    return s[min(idx, len(s) - 1)]


@dataclass
class CommandMetrics:
    invocations: int = 0
    errors: int = 0
    total_duration_s: float = 0.0
    last_duration_s: float = 0.0


class MetricsCollector:
    def __init__(self, sink_env_var: str = DEFAULT_SINK_ENV_VAR) -> None:
        self._commands: dict[str, CommandMetrics] = {}
        self._counters: dict[str, int] = {}
        self._observations: dict[str, deque[float]] = {}
        self._costs: list[dict[str, Any]] = []
        self._start_time = time.monotonic()
        self._sink_env_var = sink_env_var
        self._sink_path: Path | None = None
        self._setup_sink()

    def record(self, name: str, duration_s: float, error: bool = False) -> None:
        m = self._commands.setdefault(name, CommandMetrics())
        m.invocations += 1
        m.total_duration_s += duration_s
        m.last_duration_s = duration_s
        if error:
            m.errors += 1

    def get(self, name: str) -> CommandMetrics | None:
        return self._commands.get(name)

    def summary(self) -> dict[str, CommandMetrics]:
        return dict(self._commands)

    def reset(self) -> None:
        self._commands.clear()
        self._counters.clear()
        self._observations.clear()
        self._costs.clear()

    # --- counters ---

    def inc(self, key: str, n: int = 1) -> None:
        self._counters[key] = self._counters.get(key, 0) + n

    def reset_counter(self, key: str) -> None:
        self._counters.pop(key, None)

    # --- observations (sliding window) ---

    def observe(self, key: str, value: float) -> None:
        bucket = self._observations.setdefault(key, deque(maxlen=OBSERVATION_WINDOW))
        bucket.append(value)

    def timer(self, key: str, unit: str = "ms") -> Timer:
        """Context manager that times a block and auto-records to observations.

        unit: "ms" (default) or "s" — scales the recorded elapsed duration.
        """
        scale = 1000.0 if unit == "ms" else 1.0
        return Timer(on_exit=lambda elapsed: self.observe(key, elapsed * scale))

    # --- LLM cost tracking ---

    def cost(
        self,
        feature: str,
        model: str,
        in_tokens: int,
        out_tokens: int,
        in_rate: float = 0.0,
        out_rate: float = 0.0,
    ) -> None:
        """in_rate/out_rate are USD per MILLION tokens."""
        amount = (in_tokens / 1e6) * in_rate + (out_tokens / 1e6) * out_rate
        entry = {
            "feature": feature,
            "model": model,
            "in_tokens": in_tokens,
            "out_tokens": out_tokens,
            "amount": amount,
        }
        self._costs.append(entry)
        self.event("cost", **entry)

    # --- structured event sink (jsonl, env-gated) ---

    def event(self, kind: str, **fields: Any) -> None:
        if self._sink_path is None:
            return
        record = {"kind": kind, "ts": time.time(), **fields}
        with self._sink_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    # --- snapshots ---

    def snapshot(self) -> dict[str, Any]:
        observations = {
            key: self._stats(values) for key, values in self._observations.items()
        }
        total_cost = sum(c["amount"] for c in self._costs)
        return {
            "uptime_s": time.monotonic() - self._start_time,
            "commands": self.summary(),
            "counters": dict(self._counters),
            "observations": observations,
            "costs": list(self._costs),
            "total_cost": total_cost,
        }

    def snapshot_and_reset(self) -> dict[str, Any]:
        snap = self.snapshot()
        self.reset()
        return snap

    def format_report(self) -> str:
        snap = self.snapshot()
        lines = [f"uptime: {snap['uptime_s']:.1f}s"]
        for key, value in snap["counters"].items():
            lines.append(f"  {key}: {value}")
        for key, stats in snap["observations"].items():
            lines.append(
                f"  {key}: n={stats['n']} avg={stats['avg']:.4f} "
                f"p50={stats['p50']:.4f} p95={stats['p95']:.4f}"
            )
        if snap["costs"]:
            lines.append(f"  total_cost: ${snap['total_cost']:.4f}")
        return "\n".join(lines)

    @staticmethod
    def _stats(values: deque[float]) -> dict[str, float]:
        vals = list(values)
        if not vals:
            return {"n": 0, "p50": 0.0, "p95": 0.0, "avg": 0.0}
        return {
            "n": len(vals),
            "p50": statistics.median(vals),
            "p95": p95(vals),
            "avg": sum(vals) / len(vals),
        }

    def _setup_sink(self) -> None:
        path = os.environ.get(self._sink_env_var)
        self._sink_path = Path(path) if path else None


class Timer:
    def __init__(self, on_exit: Callable[[float], None] | None = None) -> None:
        self._start: float = 0.0
        self._on_exit = on_exit

    def __enter__(self) -> Timer:
        self._start = time.monotonic()
        return self

    def __exit__(self, *args: Any) -> None:
        if self._on_exit is not None:
            self._on_exit(self.elapsed)

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._start


_default_collector = MetricsCollector()


def get_default_collector() -> MetricsCollector:
    return _default_collector


def timed(key: str, collector: MetricsCollector | None = None) -> Callable[[F], F]:
    """Decorate a sync or async function to auto-record its duration."""

    def decorator(fn: F) -> F:
        target = collector if collector is not None else _default_collector

        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with target.timer(key):
                    return await fn(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with target.timer(key):
                return fn(*args, **kwargs)

        return sync_wrapper  # type: ignore[return-value]

    return decorator


def counted(key: str, collector: MetricsCollector | None = None) -> Callable[[F], F]:
    """Decorate a sync or async function to increment a counter on each call."""

    def decorator(fn: F) -> F:
        target = collector if collector is not None else _default_collector

        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                target.inc(key)
                return await fn(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            target.inc(key)
            return fn(*args, **kwargs)

        return sync_wrapper  # type: ignore[return-value]

    return decorator
