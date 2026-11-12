"""Extended MetricsCollector: counters, observations, cost, events, snapshots, decorators."""

from __future__ import annotations

import asyncio
import json

import pytest

from biome_mcp.metrics import MetricsCollector, counted, timed


def test_inc_increments_counter():
    mc = MetricsCollector()
    mc.inc("hits")
    mc.inc("hits", 3)
    assert mc.snapshot()["counters"]["hits"] == 4


def test_reset_counter_clears_single_key():
    mc = MetricsCollector()
    mc.inc("hits")
    mc.inc("misses")
    mc.reset_counter("hits")
    counters = mc.snapshot()["counters"]
    assert "hits" not in counters
    assert counters["misses"] == 1


def test_observe_records_sliding_window():
    mc = MetricsCollector()
    mc.observe("latency", 1.0)
    mc.observe("latency", 2.0)
    stats = mc.snapshot()["observations"]["latency"]
    assert stats["count"] == 2
    assert stats["avg"] == 1.5
    assert stats["min"] == 1.0
    assert stats["max"] == 2.0


def test_observe_window_caps_at_256():
    mc = MetricsCollector()
    for i in range(300):
        mc.observe("latency", float(i))
    stats = mc.snapshot()["observations"]["latency"]
    assert stats["count"] == 256
    # oldest values (0..43) dropped, newest kept
    assert stats["max"] == 299.0


def test_timer_auto_records_observation():
    mc = MetricsCollector()
    with mc.timer("op"):
        pass
    stats = mc.snapshot()["observations"]["op"]
    assert stats["count"] == 1
    assert stats["max"] >= 0.0


def test_cost_accumulates_amount():
    mc = MetricsCollector()
    mc.cost("ask", "haiku", in_tokens=1000, out_tokens=500, in_rate=1.0, out_rate=2.0)
    snap = mc.snapshot()
    assert len(snap["costs"]) == 1
    assert snap["costs"][0]["feature"] == "ask"
    assert snap["total_cost"] == pytest.approx(1.0 * 1 + 2.0 * 0.5)


def test_event_writes_jsonl_when_sink_configured(tmp_path, monkeypatch):
    sink = tmp_path / "events.jsonl"
    monkeypatch.setenv("BIOME_MCP_METRICS_SINK", str(sink))
    mc = MetricsCollector()
    mc.event("tool_call", name="scene.inspect", ok=True)
    lines = sink.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["kind"] == "tool_call"
    assert record["name"] == "scene.inspect"
    assert record["ok"] is True


def test_event_noop_without_sink(monkeypatch):
    monkeypatch.delenv("BIOME_MCP_METRICS_SINK", raising=False)
    mc = MetricsCollector()
    mc.event("tool_call", name="x")  # must not raise


def test_snapshot_includes_uptime_and_existing_commands():
    mc = MetricsCollector()
    mc.record("cmd", 0.1)
    snap = mc.snapshot()
    assert snap["uptime_s"] >= 0.0
    assert "counters" in snap
    assert "observations" in snap
    assert "costs" in snap


def test_snapshot_and_reset_clears_state():
    mc = MetricsCollector()
    mc.inc("hits")
    mc.observe("lat", 1.0)
    snap = mc.snapshot_and_reset()
    assert snap["counters"]["hits"] == 1
    assert mc.snapshot()["counters"] == {}
    assert mc.snapshot()["observations"] == {}


def test_format_report_contains_counters_and_observations():
    mc = MetricsCollector()
    mc.inc("hits", 5)
    mc.observe("latency", 2.0)
    report = mc.format_report()
    assert "hits: 5" in report
    assert "latency" in report


def test_timed_decorator_sync_records_observation():
    mc = MetricsCollector()

    @timed("sync.op", collector=mc)
    def add(a, b):
        return a + b

    assert add(1, 2) == 3
    assert mc.snapshot()["observations"]["sync.op"]["count"] == 1


def test_timed_decorator_async_records_observation():
    mc = MetricsCollector()

    @timed("async.op", collector=mc)
    async def add(a, b):
        return a + b

    result = asyncio.run(add(1, 2))
    assert result == 3
    assert mc.snapshot()["observations"]["async.op"]["count"] == 1


def test_counted_decorator_sync_increments():
    mc = MetricsCollector()

    @counted("sync.calls", collector=mc)
    def noop():
        return "ok"

    noop()
    noop()
    assert mc.snapshot()["counters"]["sync.calls"] == 2


def test_counted_decorator_async_increments():
    mc = MetricsCollector()

    @counted("async.calls", collector=mc)
    async def noop():
        return "ok"

    asyncio.run(noop())
    assert mc.snapshot()["counters"]["async.calls"] == 1
