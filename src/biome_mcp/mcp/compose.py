"""CompactMCP — an MCPServer subclass with schema hooks and strict argument validation."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

SchemaHook = Callable[[str, dict[str, Any]], None]


def strip_titles(tool_name: str, schema: dict[str, Any]) -> None:
    """Remove 'title' from every property and the schema root."""
    schema.pop("title", None)
    for pdef in schema.get("properties", {}).values():
        pdef.pop("title", None)


def forbid_extra_properties(tool_name: str, schema: dict[str, Any]) -> None:
    """Set additionalProperties: false if properties are present."""
    if schema.get("properties"):
        schema.setdefault("additionalProperties", False)


def inject_descriptions(
    by_tool: Mapping[str, Mapping[str, str]],
    common: Mapping[str, str] | None = None,
) -> SchemaHook:
    """Return a hook that injects param descriptions from lookup tables."""
    _common = common or {}

    def hook(tool_name: str, schema: dict[str, Any]) -> None:
        tool_descs = by_tool.get(tool_name, {})
        for pname, pdef in schema.get("properties", {}).items():
            if "description" not in pdef:
                desc = tool_descs.get(pname) or _common.get(pname)
                if desc:
                    pdef["description"] = desc

    return hook


def inject_extras(
    by_tool: Mapping[str, Mapping[str, Mapping[str, Any]]],
) -> SchemaHook:
    """Return a hook that merges extra schema keys (e.g. pattern) into params."""
    def hook(tool_name: str, schema: dict[str, Any]) -> None:
        tool_extras = by_tool.get(tool_name, {})
        for pname, pdef in schema.get("properties", {}).items():
            for k, v in tool_extras.get(pname, {}).items():
                pdef.setdefault(k, v)

    return hook


def apply_schema_hooks(mcp: MCPServer, hooks: Sequence[SchemaHook]) -> None:
    """Apply hooks to all currently registered tools."""
    for tool_name, tool in mcp._tool_manager._tools.items():
        for hook in hooks:
            hook(tool_name, tool.parameters)


class CompactMCP(MCPServer):
    """MCPServer with compact schemas and optional strict argument validation."""

    def __init__(
        self,
        name: str,
        *,
        schema_hooks: Sequence[SchemaHook] = (),
        reject_unknown_args: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(name, **kwargs)
        self._schema_hooks: tuple[SchemaHook, ...] = tuple(schema_hooks)
        self._reject_unknown_args = reject_unknown_args

    def add_tool(
        self, fn, name=None, title=None, description=None,
        annotations=None, icons=None, meta=None, structured_output=None,
    ) -> None:
        tool_name = name or fn.__name__
        if not title:
            title = tool_name.replace("_", " ").title()
        super().add_tool(
            fn, name=tool_name, title=title, description=description,
            annotations=annotations, icons=icons, meta=meta,
            structured_output=False,
        )
        tool = self._tool_manager._tools.get(tool_name)
        if tool is not None:
            for hook in self._schema_hooks:
                hook(tool_name, tool.parameters)

    async def call_tool(self, name: str, arguments: dict[str, Any], context=None) -> Any:
        if self._reject_unknown_args:
            tool = self._tool_manager.get_tool(name)
            if tool is not None and tool.parameters.get("additionalProperties") is False:
                properties = tool.parameters.get("properties", {})
                unknown = sorted(set(arguments) - set(properties))
                if unknown:
                    joined = ", ".join(unknown)
                    raise ToolError(f"unknown argument(s) for tool {name}: {joined}")
        return await super().call_tool(name, arguments, context)
