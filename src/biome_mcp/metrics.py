"""Counters + timers for command execution tracking."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class CommandMetrics:
    invocations: int = 0
    errors: int = 0
    total_duration_s: float = 0.0
    last_duration_s: float = 0.0


class MetricsCollector:
    def __init__(self) -> None:
        self._commands: dict[str, CommandMetrics] = {}

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


class Timer:
    def __init__(self) -> None:
        self._start: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.monotonic()
        return self

    def __exit__(self, *args) -> None:
        pass

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._start
