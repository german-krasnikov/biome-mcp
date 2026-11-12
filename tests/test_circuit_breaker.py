"""CircuitBreaker: consecutive-failure tracking with auto-reset cooldown."""

from __future__ import annotations

from biome_mcp.circuit_breaker import CircuitBreaker


def test_closed_initially():
    cb = CircuitBreaker()
    assert cb.is_open is False


def test_stays_closed_below_threshold():
    cb = CircuitBreaker(threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.is_open is False


def test_opens_after_threshold_failures():
    cb = CircuitBreaker(threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.is_open is True


def test_success_resets_consecutive_failure_count():
    cb = CircuitBreaker(threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_success()
    cb.record_failure()
    cb.record_failure()
    assert cb.is_open is False


def test_reset_clears_open_state():
    cb = CircuitBreaker(threshold=1)
    cb.record_failure()
    assert cb.is_open is True
    cb.reset()
    assert cb.is_open is False


def test_auto_closes_after_reset_after_elapses(monkeypatch):
    fake_time = [100.0]
    monkeypatch.setattr(
        "biome_mcp.circuit_breaker.time.monotonic", lambda: fake_time[0]
    )
    cb = CircuitBreaker(threshold=1, reset_after=10.0)
    cb.record_failure()
    assert cb.is_open is True

    fake_time[0] += 5.0
    assert cb.is_open is True

    fake_time[0] += 10.0
    assert cb.is_open is False


def test_remains_open_while_failures_keep_coming(monkeypatch):
    fake_time = [0.0]
    monkeypatch.setattr(
        "biome_mcp.circuit_breaker.time.monotonic", lambda: fake_time[0]
    )
    cb = CircuitBreaker(threshold=1, reset_after=10.0)
    cb.record_failure()
    fake_time[0] += 20.0
    assert cb.is_open is False  # cooldown elapsed, auto-reset

    cb.record_failure()
    assert cb.is_open is True
