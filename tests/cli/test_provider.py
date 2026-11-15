"""S32-S37: MCPToolProvider hooks, CB, metrics, lazy init."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from biome_mcp.circuit_breaker import CircuitBreaker
from biome_mcp.hooks import POST_HOOKS
from biome_mcp.metrics import MetricsCollector


def make_fake_mcp(tool_result: str = "ok result") -> MagicMock:
    """Minimal CompactMCP-like mock."""
    tool = MagicMock()
    tool.description = "Test tool"
    tool.parameters = {"properties": {}, "required": []}
    # No real annotations — use a plain object to avoid MagicMock truthy traps
    tool.annotations = None

    content = MagicMock()
    content.text = tool_result

    mcp = MagicMock()
    mcp._tool_manager = MagicMock()
    mcp._tool_manager._tools = {"test_tool": tool}
    mcp.call_tool = AsyncMock(return_value=[content])
    return mcp


def test_s36_list_tools_cached() -> None:
    """S36: list_tools() cached — second call returns same object."""
    from biome_mcp.cli.provider import MCPToolProvider

    mcp = make_fake_mcp()
    p = MCPToolProvider(mcp)

    tools1 = p.list_tools()
    tools2 = p.list_tools()
    assert tools1 is tools2


def test_s37_call_never_calls_list_tools() -> None:
    """S37: call_tool_sync never calls list_tools()."""
    from biome_mcp.cli.provider import MCPToolProvider

    mcp = make_fake_mcp("pong")
    p = MCPToolProvider(mcp)

    list_calls: list[int] = []
    original_list = p.list_tools.__func__  # type: ignore[attr-defined]

    def patched_list() -> list:
        list_calls.append(1)
        return original_list(p)

    p.list_tools = patched_list  # type: ignore[method-assign]

    p.call_tool_sync("test_tool", {})
    assert list_calls == []


def test_s32_hooks_called_after_call() -> None:
    """S32: call_tool_sync calls run_post_hooks."""
    from biome_mcp.cli.provider import MCPToolProvider

    hook_calls: list[tuple[str, str]] = []

    async def my_hook(cmd: str, args: dict, result: str, mw: object) -> str:
        hook_calls.append((cmd, result))
        return result

    POST_HOOKS.setdefault("test_tool", []).append(my_hook)
    try:
        mcp = make_fake_mcp("hook result")
        p = MCPToolProvider(mcp)
        p.call_tool_sync("test_tool", {})
        assert len(hook_calls) == 1
        assert hook_calls[0][0] == "test_tool"
    finally:
        POST_HOOKS.get("test_tool", []).remove(my_hook)


def test_s33_cb_open_fast_fail() -> None:
    """S33: CB OPEN → returns error without calling mcp.call_tool."""
    from biome_mcp.cli.provider import MCPToolProvider

    mcp = make_fake_mcp()
    cb = CircuitBreaker(threshold=1)
    cb.record_failure()  # one failure at threshold=1 → OPEN

    p = MCPToolProvider(mcp, circuit_breaker=cb)
    result = p.call_tool_sync("test_tool", {})

    assert result.error_code is not None or result.status.value == "failed"
    mcp.call_tool.assert_not_called()


def test_s34_cb_records_success() -> None:
    """S34: CB records success after successful call."""
    from biome_mcp.cli.provider import MCPToolProvider

    mcp = make_fake_mcp("ok")
    cb = CircuitBreaker()

    p = MCPToolProvider(mcp, circuit_breaker=cb)
    p.call_tool_sync("test_tool", {})

    assert cb.state == CircuitBreaker.CLOSED
    assert cb.failures == 0


def test_s35_metrics_timer_records() -> None:
    """S35: call_tool_sync records to metrics timer observations."""
    from biome_mcp.cli.provider import MCPToolProvider

    mcp = make_fake_mcp("val")
    collector = MetricsCollector()

    p = MCPToolProvider(mcp, metrics=collector)
    p.call_tool_sync("test_tool", {})

    assert "cli.test_tool" in collector._observations
