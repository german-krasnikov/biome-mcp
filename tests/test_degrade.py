"""TDD tests for degrade.py — generic graceful degradation ladder.

metrics is injected (duck-typed: .inc(key) / .event(kind, **fields)), not a
module singleton — callers bind their own MetricsCollector instance.
"""
import pytest

from biome_mcp.degrade import degrade, wrap_degraded
from biome_mcp.metrics import MetricsCollector

# ── Test 1: all steps fail → no_fallback surface marker ──────────────────────

async def test_all_steps_fail_no_fallback():
    mc = MetricsCollector()

    step_name, value = await degrade("x", [("a", lambda: None), ("b", lambda: None)], metrics=mc)

    assert step_name == "b"
    assert value is None
    assert mc.snapshot()["counters"].get("degraded.x", 0) == 1
    marker = wrap_degraded("x", "b", None)
    assert marker == "[DEGRADED:x:b:no_fallback]"


# ── Test 2: first step succeeds → no metrics, no marker ──────────────────────

async def test_first_step_succeeds_no_metrics():
    mc = MetricsCollector()

    step_name, value = await degrade(
        "x", [("primary", lambda: "hello"), ("fallback", lambda: "world")], metrics=mc
    )

    assert step_name == "primary"
    assert value == "hello"
    assert mc.snapshot()["counters"].get("degraded.x", 0) == 0


# ── Test 3: mix async and sync steps ─────────────────────────────────────────

async def test_async_and_sync_steps():
    async def async_fail():
        return None

    def sync_success():
        return "sync_result"

    step_name, value = await degrade(
        "mixed", [("async_step", async_fail), ("sync_step", sync_success)]
    )

    assert step_name == "sync_step"
    assert value == "sync_result"


# ── Test 4: step raises exception → caught, treated as failure ────────────────

async def test_step_raises_exception_caught():
    mc = MetricsCollector()
    events = []
    mc.event = lambda kind, **fields: events.append({"kind": kind, **fields})

    def boom():
        raise RuntimeError("boom")

    step_name, value = await degrade(
        "exc_test", [("raiser", boom), ("ok", lambda: "safe")], metrics=mc
    )
    assert step_name == "ok"
    assert value == "safe"
    assert any(e.get("reason", "").startswith("raised:RuntimeError") for e in events)


# ── Test 5: env disabled → exception bubbles raw ─────────────────────────────

async def test_env_disabled_propagates_exception(monkeypatch):
    monkeypatch.setenv("BIOME_MCP_DEGRADE_DISABLED", "1")

    def explode():
        raise ValueError("raw error")

    with pytest.raises(ValueError, match="raw error"):
        await degrade("feat", [("s1", explode), ("s2", lambda: "ok")])


# ── Test 5b: custom disabled_env name is respected ───────────────────────────

async def test_custom_disabled_env_name(monkeypatch):
    monkeypatch.setenv("MY_APP_DEGRADE_DISABLED", "1")

    def explode():
        raise ValueError("raw!")

    with pytest.raises(ValueError, match="raw!"):
        await degrade("feat", [("s1", explode)], disabled_env="MY_APP_DEGRADE_DISABLED")


# ── Test 6: metrics=None is a safe no-op (no AttributeError) ────────────────

async def test_no_metrics_is_safe_noop():
    step_name, value = await degrade("visual_diff", [
        ("budget_day_cap_exceeded", lambda: None),
        ("pixel_only", lambda: "px_result"),
    ])
    assert step_name == "pixel_only"
    assert value == "px_result"

    marker_fail = wrap_degraded("visual_diff", "budget_day_cap_exceeded", None)
    assert marker_fail == "[DEGRADED:visual_diff:budget_day_cap_exceeded:no_fallback]"
    marker_ok = wrap_degraded("visual_diff", "budget_day_cap_exceeded", "px_result")
    assert "[DEGRADED:visual_diff:budget_day_cap_exceeded]" in marker_ok
    assert "no_fallback" not in marker_ok


# ── Test 9: counter cardinality — one feature × N steps ──────────────────────

async def test_counter_cardinality_per_step():
    mc = MetricsCollector()

    await degrade("card_test", [
        ("step_a", lambda: None),
        ("step_b", lambda: None),
        ("step_c", lambda: "ok"),
    ], metrics=mc)

    snap = mc.snapshot()["counters"]
    assert snap.get("degraded.card_test.step_a", 0) == 1
    assert snap.get("degraded.card_test.step_b", 0) == 1
    assert snap.get("degraded.card_test.step_c", 0) == 0
    assert snap.get("degraded.card_test", 0) == 1


# ── Test 10: event log format ─────────────────────────────────────────────────

async def test_event_log_format():
    mc = MetricsCollector()
    events = []
    mc.event = lambda kind, **fields: events.append({"kind": kind, **fields})

    await degrade("evt_feat", [("s1", lambda: None), ("s2", lambda: "ok")], metrics=mc)

    degraded_events = [e for e in events if e["kind"] == "degraded"]
    assert len(degraded_events) == 1
    e = degraded_events[0]
    assert e["feature"] == "evt_feat"
    assert e["step"] == "s1"
    assert "reason" in e


# ── Test 11: wrap_degraded prefix exactly once ────────────────────────────────

def test_wrap_degraded_prefix_not_doubled():
    result = wrap_degraded("feat", "step", "value")
    assert result.count("[DEGRADED:") == 1
    assert result.startswith("[DEGRADED:feat:step]\n")


# ── Test 13: disabled mode falls through None to next rung ───────────────────

async def test_disabled_mode_falls_through_on_none(monkeypatch):
    monkeypatch.setenv("BIOME_MCP_DEGRADE_DISABLED", "1")

    step_name, result = await degrade("feat", [
        ("s1", lambda: None),
        ("s2", lambda: "ok"),
    ])
    assert result == "ok"
    assert step_name == "s2"


# ── Test 14: disabled mode exception still propagates raw ─────────────────────

async def test_disabled_mode_propagates_exception_raw(monkeypatch):
    monkeypatch.setenv("BIOME_MCP_DEGRADE_DISABLED", "1")

    def explode():
        raise ValueError("raw!")

    with pytest.raises(ValueError, match="raw!"):
        await degrade("feat", [("boom", explode), ("fallback", lambda: "safe")])


# ── Test 15: disabled mode → metrics.event NOT fired ─────────────────────────

async def test_disabled_mode_no_metrics_event(monkeypatch):
    mc = MetricsCollector()
    monkeypatch.setenv("BIOME_MCP_DEGRADE_DISABLED", "1")

    events = []
    monkeypatch.setattr(
        mc, "event", lambda kind, **fields: events.append({"kind": kind, **fields})
    )

    await degrade("dis_feat", [
        ("s1", lambda: None),
        ("s2", lambda: "ok"),
    ], metrics=mc)

    assert events == [], f"Expected no events, got {events}"


async def test_disabled_mode_no_metrics_event_all_fail(monkeypatch):
    mc = MetricsCollector()
    monkeypatch.setenv("BIOME_MCP_DEGRADE_DISABLED", "1")

    events = []
    monkeypatch.setattr(
        mc, "event", lambda kind, **fields: events.append({"kind": kind, **fields})
    )

    await degrade("dis_all_fail", [
        ("s1", lambda: None),
        ("s2", lambda: None),
    ], metrics=mc)

    assert events == [], f"Expected no events, got {events}"


# ── Test 16: empty steps list → ("", None), no metrics ──────────────────────

async def test_empty_steps_list_returns_empty_name_none():
    mc = MetricsCollector()

    step_name, value = await degrade("empty_feat", [], metrics=mc)

    assert step_name == ""
    assert value is None
    snap = mc.snapshot()["counters"]
    assert snap.get("degraded.empty_feat", 0) == 0


# ── Test 17: disabled + async step falls through correctly ───────────────────

async def test_disabled_async_step_falls_through(monkeypatch):
    monkeypatch.setenv("BIOME_MCP_DEGRADE_DISABLED", "1")

    async def async_none():
        return None

    step_name, value = await degrade("feat", [
        ("async_step", async_none),
        ("fallback", lambda: "ok"),
    ])

    assert step_name == "fallback"
    assert value == "ok"


# ── Test 12: all steps raise → last step name returned, counter=1 ─────────────

async def test_all_steps_raise_all_caught():
    mc = MetricsCollector()

    step_name, value = await degrade("all_raise", [
        ("s1", lambda: (_ for _ in ()).throw(OSError("disk"))),
        ("s2", lambda: (_ for _ in ()).throw(OSError("net"))),
    ], metrics=mc)

    assert step_name == "s2"
    assert value is None
    assert mc.snapshot()["counters"].get("degraded.all_raise", 0) == 1
