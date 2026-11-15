"""MCPToolProvider — bridges CompactMCP to ToolProvider Protocol.

This is the ONLY file in cli/ that imports mcp. Guard with try/except.
"""
from __future__ import annotations

import asyncio
from contextlib import nullcontext
from typing import Any

from biome_mcp.cli.app import ToolInfo
from biome_mcp.errors import BiomeError, ErrorCode
from biome_mcp.hooks import run_post_hooks
from biome_mcp.models.result import CommandResult

try:
    from biome_mcp.mcp.compose import CompactMCP
except ImportError:
    CompactMCP = None  # type: ignore[assignment,misc]

try:
    from biome_mcp.circuit_breaker import CircuitBreaker
except ImportError:
    CircuitBreaker = None  # type: ignore[assignment,misc]

try:
    from biome_mcp.metrics import MetricsCollector
except ImportError:
    MetricsCollector = None  # type: ignore[assignment,misc]


def _flatten_result(raw: Any) -> str:
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        return "\n".join(
            item.text if hasattr(item, "text") else str(item) for item in raw
        )
    if hasattr(raw, "text"):
        return raw.text
    return str(raw)


def _extract_effect(tool: Any) -> str | None:
    ann = getattr(tool, "annotations", None)
    if ann is None:
        return None
    if getattr(ann, "readOnlyHint", False):
        return "read"
    if getattr(ann, "destructiveHint", False):
        return "delete"
    return "write"


def _extract_namespace(name: str) -> str:
    for sep in ("_", "."):
        if sep in name:
            return name.split(sep)[0]
    return name


class MCPToolProvider:
    """Wraps CompactMCP, adds hooks, circuit breaker, and metrics."""

    def __init__(
        self,
        mcp: Any,
        *,
        metrics: Any = None,
        circuit_breaker: Any = None,
        registry: Any = None,
    ) -> None:
        self._mcp = mcp
        self._metrics = metrics
        self._cb = circuit_breaker
        self._registry = registry
        self._tools_cache: list[ToolInfo] | None = None

    def list_tools(self) -> list[ToolInfo]:
        if self._tools_cache is None:
            self._tools_cache = [
                self._make_tool_info(name, tool)
                for name, tool in self._mcp._tool_manager._tools.items()
            ]
        return self._tools_cache

    def get_tool(self, name: str) -> ToolInfo | None:
        """O(1) direct dict lookup — never calls list_tools."""
        tool = self._mcp._tool_manager._tools.get(name)
        if tool is None:
            return None
        return self._make_tool_info(name, tool)

    def call_tool_sync(self, name: str, args: dict[str, Any]) -> CommandResult:
        # Async guard
        try:
            asyncio.get_running_loop()
            raise BiomeError(
                ErrorCode.INTERNAL_ERROR,
                "CLI called from async context — use await directly",
            )
        except RuntimeError:
            pass  # No running loop — safe to proceed

        # Circuit breaker fast-fail
        if self._cb is not None and not self._cb.allow_request():
            return CommandResult.error(
                ErrorCode.CONNECTION_LOST,
                f"circuit open, retry in {self._cb.remaining():.0f}s",
            )

        ctx = self._metrics.timer(f"cli.{name}") if self._metrics else nullcontext()

        try:
            with ctx:
                text = asyncio.run(self._call_async(name, args))
            if self._cb is not None:
                self._cb.record_success()
            return CommandResult.ok(text)
        except Exception as exc:
            if self._cb is not None:
                self._cb.record_failure()
            if isinstance(exc, BiomeError):
                return CommandResult.error(exc.code, exc.message)
            return CommandResult.error(ErrorCode.INTERNAL_ERROR, str(exc))

    async def _call_async(self, name: str, args: dict[str, Any]) -> str:
        raw = await self._mcp.call_tool(name, args)
        text = _flatten_result(raw)
        return await run_post_hooks(name, args, text, None)

    def _make_tool_info(self, name: str, tool: Any) -> ToolInfo:
        info: ToolInfo = {
            "name": name,
            "description": getattr(tool, "description", "") or "",
            "input_schema": dict(getattr(tool, "parameters", {})),
        }
        effect = _extract_effect(tool)
        if effect is not None:
            info["effect"] = effect
        ns = _extract_namespace(name)
        info["namespace"] = ns
        return info
