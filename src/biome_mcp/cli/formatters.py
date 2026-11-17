"""List/describe formatting and filter helpers — engine-agnostic."""
from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from biome_mcp.cli.app import ToolInfo, ToolProvider

_DESCRIPTION_MAX_LEN = 72


def matches_ns(t: ToolInfo, ns: str | None) -> bool:
    if ns is None:
        return True
    tool_ns: str | None = t.get("namespace")  # type: ignore[assignment]
    if tool_ns is not None:
        return tool_ns == ns
    name = t["name"]
    return name == ns or name.startswith(ns + "_") or name.startswith(ns + ".")


def matches_effect(t: ToolInfo, effect: str | None) -> bool:
    if effect is None:
        return True
    tool_effect: str | None = t.get("effect")  # type: ignore[assignment]
    if tool_effect is None:
        return True
    if effect == "read":
        return tool_effect == "read"
    if effect == "write":
        return tool_effect in ("write", "idempotent_write", "delete")
    return tool_effect == effect


def matches_grep(t: ToolInfo, grep: str | None) -> bool:
    if grep is None:
        return True
    q = grep.lower()
    return q in t["name"].lower() or q in t["description"].lower()


def print_flat(tools: list[ToolInfo]) -> None:
    if not tools:
        return
    width = max(len(t["name"]) for t in tools) + 2
    for t in tools:
        print(f"{t['name']:<{width}}{t['description'][:_DESCRIPTION_MAX_LEN]}")


def print_grouped(tools: list[ToolInfo]) -> None:
    groups: dict[str, list[ToolInfo]] = {}
    for t in tools:
        ns: str = t.get("namespace") or t["name"].split("_")[0]  # type: ignore[assignment]
        groups.setdefault(ns, []).append(t)
    for ns, members in groups.items():
        print(f"\n{ns} ({len(members)})")
        print_flat(members)


def render_tool_info(info: ToolInfo) -> str:
    lines = [f"== {info['name']} ==", info["description"]]
    effect = info.get("effect")  # type: ignore[misc]
    if effect:
        lines.append(f"Effect: {effect}")
    schema = info.get("input_schema") or {}
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    if props:
        lines.append("")
        lines.append("Parameters:")
        width = max(len(n) for n in props) + 1
        for pname, pdef in props.items():
            ptype = pdef.get("type", "any")
            star = "*" if pname in required else " "
            enum = pdef.get("enum")
            suffix = f"  ({','.join(str(e) for e in enum)})" if enum else ""
            lines.append(f"  {pname + star:<{width + 1}} {ptype}{suffix}")
    example = generate_example(info)
    if example:
        lines.append("")
        lines.append(f"Example: {example}")
    return "\n".join(lines)


def suggest_tool(name: str, provider: ToolProvider) -> str | None:
    """Return closest tool name or None."""
    names = [t["name"] for t in provider.list_tools()]
    matches = difflib.get_close_matches(name, names, n=1, cutoff=0.6)
    return matches[0] if matches else None


def tools_by_ns_prefix(prefix: str, provider: ToolProvider) -> list[ToolInfo]:
    """Return tools whose namespace or name starts with prefix."""
    return [t for t in provider.list_tools() if matches_ns(t, prefix)]


def validate_required(info: ToolInfo, args: dict) -> list[str]:
    """Return list of missing required parameter names."""
    schema = info.get("input_schema") or {}
    required = schema.get("required", [])
    return [r for r in required if r not in args]


def generate_example(info: ToolInfo, app_name: str = "") -> str:
    """Generate example invocation from schema."""
    schema = info.get("input_schema") or {}
    props = schema.get("properties", {})
    if not props:
        return ""
    parts = [f"{app_name} {info['name']}"] if app_name else [info["name"]]
    for pname, pdef in props.items():
        enum = pdef.get("enum")
        if enum:
            parts.append(f"{pname}={enum[0]}")
        elif pdef.get("type") == "integer":
            parts.append(f"{pname}=0")
        elif pdef.get("type") == "boolean":
            parts.append(f"{pname}=true")
        else:
            parts.append(f"{pname}=<{pdef.get('type', 'value')}>")
    return " ".join(parts)
