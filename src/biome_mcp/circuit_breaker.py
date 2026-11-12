"""CircuitBreaker — trip open after consecutive failures, auto-reset after cooldown."""

from __future__ import annotations

import time


class CircuitBreaker:
    """Track consecutive failures, open when threshold reached."""

    def __init__(self, threshold: int = 3, reset_after: float = 30.0) -> None:
        self._threshold = threshold
        self._reset_after = reset_after
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._threshold and self._opened_at is None:
            self._opened_at = time.monotonic()

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at >= self._reset_after:
            self.reset()
            return False
        return True

    def reset(self) -> None:
        self._consecutive_failures = 0
        self._opened_at = None
