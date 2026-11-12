"""CircuitBreaker — CLOSED/OPEN/HALF_OPEN with external readiness check."""

from __future__ import annotations

import time
from collections.abc import Callable


class CircuitBreaker:
    CLOSED, OPEN, HALF_OPEN = 0, 1, 2

    def __init__(
        self,
        threshold: int = 3,
        cooldown: float = 15.0,
        is_ready_fn: Callable[[], bool] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.state = self.CLOSED
        self.failures = 0
        self.threshold = threshold
        self.cooldown = cooldown
        self.opened_at = 0.0
        self._probe_in_flight: bool = False
        self._is_ready_fn = is_ready_fn
        self._clock = clock

    def record_success(self) -> None:
        self.failures = 0
        self.state = self.CLOSED
        self._probe_in_flight = False

    def release_probe(self) -> None:
        self._probe_in_flight = False

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = self.OPEN
            self.opened_at = self._clock()

    def allow_request(self) -> bool:
        if self.state == self.CLOSED:
            return True
        if self.state == self.OPEN:
            if self._is_ready_fn is not None:
                try:
                    if self._is_ready_fn():
                        self.state = self.HALF_OPEN
                        self._probe_in_flight = True
                        return True
                except Exception:
                    pass
            if self._clock() - self.opened_at > self.cooldown:
                self.state = self.HALF_OPEN
                self._probe_in_flight = True
                return True
            return False
        return True

    def get_status(self) -> str:
        return ["CLOSED", "OPEN", "HALF_OPEN"][self.state]

    def remaining(self) -> float:
        return max(0.0, self.cooldown - (self._clock() - self.opened_at))

    @property
    def is_open(self) -> bool:
        return not self.allow_request()

    def reset(self) -> None:
        self.state = self.CLOSED
        self.failures = 0
        self.opened_at = 0.0
        self._probe_in_flight = False
