"""Stage 3: Metrics tests."""

from biome_mcp.metrics import MetricsCollector, Timer


def test_record_and_get():
    mc = MetricsCollector()
    mc.record("test.cmd", 0.5)
    m = mc.get("test.cmd")
    assert m is not None
    assert m.invocations == 1
    assert m.total_duration_s == 0.5


def test_record_errors():
    mc = MetricsCollector()
    mc.record("test.cmd", 0.1, error=True)
    mc.record("test.cmd", 0.2, error=False)
    m = mc.get("test.cmd")
    assert m.invocations == 2
    assert m.errors == 1


def test_reset():
    mc = MetricsCollector()
    mc.record("test.cmd", 0.1)
    mc.reset()
    assert mc.get("test.cmd") is None


def test_summary():
    mc = MetricsCollector()
    mc.record("a", 0.1)
    mc.record("b", 0.2)
    s = mc.summary()
    assert "a" in s
    assert "b" in s


def test_timer():
    with Timer() as t:
        pass
    assert t.elapsed >= 0
