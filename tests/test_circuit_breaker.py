"""CircuitBreaker: CLOSED/OPEN/HALF_OPEN with readiness check and injectable clock."""

from __future__ import annotations

from biome_mcp.circuit_breaker import CircuitBreaker


def _make_clock(start: float = 100.0):
    t = [start]

    def clock():
        return t[0]

    def advance(seconds: float):
        t[0] += seconds

    return clock, advance


def test_closed_initially():
    cb = CircuitBreaker()
    assert cb.state == CircuitBreaker.CLOSED
    assert cb.allow_request() is True
    assert cb.is_open is False


def test_stays_closed_below_threshold():
    cb = CircuitBreaker(threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.allow_request() is True


def test_opens_after_threshold_failures():
    cb = CircuitBreaker(threshold=3)
    for _ in range(3):
        cb.record_failure()
    assert cb.state == CircuitBreaker.OPEN
    assert cb.allow_request() is False
    assert cb.is_open is True


def test_success_resets():
    cb = CircuitBreaker(threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_success()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitBreaker.CLOSED


def test_cooldown_transitions_to_half_open():
    clock, advance = _make_clock()
    cb = CircuitBreaker(threshold=1, cooldown=10.0, clock=clock)
    cb.record_failure()
    assert cb.allow_request() is False

    advance(11.0)
    assert cb.allow_request() is True
    assert cb.state == CircuitBreaker.HALF_OPEN


def test_half_open_allows_concurrent():
    clock, advance = _make_clock()
    cb = CircuitBreaker(threshold=1, cooldown=5.0, clock=clock)
    cb.record_failure()
    advance(6.0)
    assert cb.allow_request() is True
    assert cb.allow_request() is True  # concurrent OK in HALF_OPEN


def test_half_open_success_closes():
    clock, advance = _make_clock()
    cb = CircuitBreaker(threshold=1, cooldown=5.0, clock=clock)
    cb.record_failure()
    advance(6.0)
    cb.allow_request()
    cb.record_success()
    assert cb.state == CircuitBreaker.CLOSED


def test_half_open_failure_reopens():
    clock, advance = _make_clock()
    cb = CircuitBreaker(threshold=1, cooldown=5.0, clock=clock)
    cb.record_failure()
    advance(6.0)
    cb.allow_request()
    cb.record_failure()
    assert cb.state == CircuitBreaker.OPEN


def test_is_ready_fn_triggers_half_open():
    ready = [False]
    cb = CircuitBreaker(threshold=1, cooldown=999.0, is_ready_fn=lambda: ready[0])
    cb.record_failure()
    assert cb.allow_request() is False

    ready[0] = True
    assert cb.allow_request() is True
    assert cb.state == CircuitBreaker.HALF_OPEN


def test_is_ready_fn_exception_swallowed():
    def boom():
        raise RuntimeError("oops")

    clock, advance = _make_clock()
    cb = CircuitBreaker(threshold=1, cooldown=999.0, is_ready_fn=boom, clock=clock)
    cb.record_failure()
    assert cb.allow_request() is False  # exception swallowed, still OPEN


def test_release_probe():
    clock, advance = _make_clock()
    cb = CircuitBreaker(threshold=1, cooldown=5.0, clock=clock)
    cb.record_failure()
    advance(6.0)
    cb.allow_request()
    assert cb._probe_in_flight is True
    cb.release_probe()
    assert cb._probe_in_flight is False


def test_get_status():
    cb = CircuitBreaker(threshold=1)
    assert cb.get_status() == "CLOSED"
    cb.record_failure()
    assert cb.get_status() == "OPEN"


def test_remaining():
    clock, advance = _make_clock()
    cb = CircuitBreaker(threshold=1, cooldown=10.0, clock=clock)
    cb.record_failure()
    assert cb.remaining() == 10.0
    advance(3.0)
    assert cb.remaining() == 7.0
    advance(10.0)
    assert cb.remaining() == 0.0


def test_reset():
    cb = CircuitBreaker(threshold=1)
    cb.record_failure()
    assert cb.is_open is True
    cb.reset()
    assert cb.is_open is False
    assert cb.state == CircuitBreaker.CLOSED


def test_backward_compat_is_open():
    """is_open property wraps allow_request for old API."""
    clock, advance = _make_clock()
    cb = CircuitBreaker(threshold=1, cooldown=10.0, clock=clock)
    cb.record_failure()
    assert cb.is_open is True
    advance(11.0)
    assert cb.is_open is False
