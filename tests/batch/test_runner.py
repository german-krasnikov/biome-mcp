"""Stage 2: Batch runner tests."""

import pytest

from biome_mcp.batch.parser import parse_batch
from biome_mcp.batch.runner import run_batch
from biome_mcp.errors import BiomeError, ErrorCode
from biome_mcp.models.descriptor import CommandDescriptor, CommandEffect
from biome_mcp.models.result import CommandResult, CommandStatus
from biome_mcp.registry import Registry


def _desc(name, effect=CommandEffect.READ):
    return CommandDescriptor(
        name=name, namespace=name.split(".")[0], summary=name, params=(),
        effect=effect,
    )


def _make_registry(*descriptors):
    reg = Registry()
    for d in descriptors:
        reg.register(d)
    return reg


@pytest.mark.asyncio
async def test_runner_stops_on_error():
    order = []

    async def handler(name, args):
        if name == "test.fail":
            order.append("fail")
            raise BiomeError(ErrorCode.INTERNAL_ERROR, "boom")
        order.append("ok")
        return CommandResult.ok("ok")

    reg = _make_registry(_desc("test.fail"), _desc("test.ok"))
    doc = parse_batch("test.fail x=1\ntest.ok x=2")
    results = await run_batch(reg, doc, handler)
    assert len(results) == 1
    assert results[0].result.status == CommandStatus.FAILED
    assert order == ["fail"]


@pytest.mark.asyncio
async def test_runner_continues_on_transient_read():
    order = []

    async def handler(name, args):
        if name == "test.timeout":
            order.append("timeout")
            return CommandResult.error(ErrorCode.TIMEOUT, "timed out")
        order.append("ok")
        return CommandResult.ok("ok")

    reg = _make_registry(_desc("test.timeout"), _desc("test.ok"))
    doc = parse_batch("test.timeout x=1\ntest.ok x=2")
    results = await run_batch(reg, doc, handler)
    # timeout → error_class=transient, effect=read → batch_policy=continue
    assert len(results) == 2
    assert order == ["timeout", "ok"]


@pytest.mark.asyncio
async def test_runner_all_ok():
    async def handler(name, args):
        return CommandResult.ok("done")

    reg = _make_registry(_desc("test.a"), _desc("test.b"))
    doc = parse_batch("test.a x=1\ntest.b x=2")
    results = await run_batch(reg, doc, handler)
    assert len(results) == 2
    assert all(r.result.status == CommandStatus.OK for r in results)


@pytest.mark.asyncio
async def test_runner_write_transient_stops():
    """Write commands with transient errors should STOP, not continue."""
    order = []

    async def handler(name, args):
        if name == "test.timeout":
            order.append("timeout")
            return CommandResult.error(ErrorCode.TIMEOUT, "timed out")
        order.append("ok")
        return CommandResult.ok("ok")

    reg = _make_registry(
        _desc("test.timeout", effect=CommandEffect.WRITE),
        _desc("test.ok"),
    )
    doc = parse_batch("test.timeout x=1\ntest.ok x=2")
    results = await run_batch(reg, doc, handler)
    # write + transient → stop (not continue like read + transient)
    assert len(results) == 1
    assert order == ["timeout"]


@pytest.mark.asyncio
async def test_runner_preserves_step_ids():
    async def handler(name, args):
        return CommandResult.ok("done")

    reg = _make_registry(_desc("test.a"), _desc("test.b"))
    doc = parse_batch("first: test.a x=1\nsecond: test.b x=2")
    results = await run_batch(reg, doc, handler)
    assert results[0].step_id == "first"
    assert results[1].step_id == "second"
