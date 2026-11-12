"""Stage 2: Executor tests — handler passed as callback."""

import pytest

from biome_mcp.errors import BiomeError, ErrorCode
from biome_mcp.executor import Executor
from biome_mcp.guards import GuardResult
from biome_mcp.models.descriptor import CommandDescriptor, CommandEffect, ParamSpec
from biome_mcp.models.result import CommandResult, CommandStatus
from biome_mcp.registry import Registry


def _reg(*descriptors):
    reg = Registry()
    for d in descriptors:
        reg.register(d)
    return reg


def _desc(name, params=(), effect=CommandEffect.READ):
    return CommandDescriptor(
        name=name, namespace=name.split(".")[0], summary=name, params=params,
    )


@pytest.mark.asyncio
async def test_execute_ok():
    async def handler(args):
        return CommandResult.ok(f"got {args.get('x')}")

    reg = _reg(_desc("test.echo"))
    ex = Executor(reg)
    result = await ex.execute("test.echo", {"x": 42}, handler)
    assert result.status == CommandStatus.OK
    assert "42" in result.text


@pytest.mark.asyncio
async def test_execute_invalid_args():
    async def handler(args):
        return CommandResult.ok("ok")

    desc = _desc("test.need_path", params=(
        ParamSpec(name="path", param_type=str),
    ))
    reg = _reg(desc)
    ex = Executor(reg)
    result = await ex.execute("test.need_path", {}, handler)
    assert result.status == CommandStatus.FAILED
    assert "path" in result.text


@pytest.mark.asyncio
async def test_guard_blocks_execution():
    call_count = 0

    async def handler(args):
        nonlocal call_count
        call_count += 1
        return CommandResult.ok("ok")

    class DenyAll:
        async def check(self, cmd, args):
            return GuardResult.deny("nope")

    reg = _reg(_desc("test.guarded"))
    ex = Executor(reg, guards=[DenyAll()])
    result = await ex.execute("test.guarded", {}, handler)
    assert result.status == CommandStatus.CANCELLED
    assert call_count == 0


@pytest.mark.asyncio
async def test_execute_unknown_command():
    async def handler(args):
        return CommandResult.ok("ok")

    reg = Registry()
    ex = Executor(reg)
    result = await ex.execute("nonexistent", {}, handler)
    assert result.status == CommandStatus.FAILED
    assert "nonexistent" in result.text


@pytest.mark.asyncio
async def test_execute_batch_sequential():
    order = []

    async def handler_a(args):
        order.append("a")
        return CommandResult.ok("a done")

    async def handler_b(args):
        order.append("b")
        return CommandResult.ok("b done")

    handlers = {"test.a": handler_a, "test.b": handler_b}
    reg = _reg(_desc("test.a"), _desc("test.b"))
    ex = Executor(reg)
    results = await ex.execute_batch([
        ("test.a", {}, handlers["test.a"]),
        ("test.b", {}, handlers["test.b"]),
    ])
    assert len(results) == 2
    assert order == ["a", "b"]
    assert all(r.status == CommandStatus.OK for r in results)


@pytest.mark.asyncio
async def test_execute_batch_stops_on_error():
    order = []

    async def fail_handler(args):
        order.append("fail")
        raise BiomeError(ErrorCode.INTERNAL_ERROR, "boom")

    async def ok_handler(args):
        order.append("ok")
        return CommandResult.ok("ok")

    reg = _reg(_desc("test.fail"), _desc("test.ok"))
    ex = Executor(reg)
    results = await ex.execute_batch([
        ("test.fail", {}, fail_handler),
        ("test.ok", {}, ok_handler),
    ])
    assert len(results) == 1
    assert results[0].status == CommandStatus.FAILED
    assert order == ["fail"]
