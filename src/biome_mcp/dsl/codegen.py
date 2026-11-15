"""Generate Python source from parsed TOOL declarations."""
from __future__ import annotations

import json as _json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .parser import ParamDecl, ToolDecl

_PY_TYPE = {"str": "str", "int": "int", "float": "float", "bool": "bool", "list": "list"}
_JSON_TYPE = {
    "str": "string", "int": "integer", "float": "number",
    "bool": "boolean", "list": "array",
}


def _const_name(tool_name: str) -> str:
    return tool_name.replace(".", "_").upper()


def gen_descriptors(tools: list[ToolDecl]) -> str:
    lines = [
        '"""Generated tool descriptors — DO NOT EDIT."""',
        "from biome_mcp.models.descriptor import CommandDescriptor, CommandEffect, ParamSpec",
        "",
    ]
    for t in tools:
        ns = t.namespace
        params = ",\n        ".join(_descriptor_param(p) for p in t.params)
        effect = f"CommandEffect.{t.effect.upper()}"
        lines.append(f"{_const_name(t.name)} = CommandDescriptor(")
        lines.append(f'    name="{t.name}",')
        lines.append(f'    namespace="{ns}",')
        lines.append(f"    summary={t.summary!r},")
        if params:
            lines.append(f"    params=(\n        {params},\n    ),")
        else:
            lines.append("    params=(),")
        lines.append(f"    effect={effect},")
        lines.append(f"    batchable={t.batchable},")
        lines.append(f"    blast_radius={t.blast_radius},")
        lines.append(")")
        lines.append("")
    return "\n".join(lines)


def _descriptor_param(p: ParamDecl) -> str:
    parts = [f'"{p.name}", {_PY_TYPE[p.param_type]}']
    parts.append(f"required={p.required}")
    if p.default is not None:
        parts.append(f"default={_coerce_default(p)}")
    parts.append(f"description={p.description!r}")
    return f"ParamSpec({', '.join(parts)})"


def _coerce_default(p: ParamDecl) -> str:
    if p.param_type == "int":
        return p.default  # type: ignore[return-value]
    if p.param_type == "float":
        return p.default  # type: ignore[return-value]
    if p.param_type == "bool":
        return "True" if p.default.lower() in ("true", "yes") else "False"  # type: ignore[union-attr]
    return f'"{p.default}"'


def gen_schema_init(tools: list[ToolDecl]) -> str:
    lines = [
        '"""Generated schema registry init — DO NOT EDIT."""',
        "",
        "",
        "def init(registry):",
    ]
    for t in tools:
        props = _json_properties(t.params)
        req_names = ", ".join(f'"{p.name}"' for p in t.params if p.required)
        schema = "{"
        schema += '"type": "object", '
        schema += f'"properties": {props}, '
        schema += f'"required": [{req_names}], '
        schema += '"additionalProperties": False'
        schema += "}"
        lines.append(f"    registry.capture(\"{t.name}\", {schema}, {_json.dumps(t.summary)})")
    return "\n".join(lines) + "\n"


def _json_properties(params: list[ParamDecl]) -> str:
    parts = []
    for p in params:
        jtype = _JSON_TYPE[p.param_type]
        desc_json = _json.dumps(p.description)
        entry = f'"{p.name}": {{"type": "{jtype}", "description": {desc_json}}}'
        parts.append(entry)
    return "{" + ", ".join(parts) + "}"


def gen_help_text(tools: list[ToolDecl]) -> str:
    blocks = []
    for t in tools:
        lines = [f"== {t.name} ==", t.summary]
        if t.effect != "read":
            lines[-1] += f" [{t.effect.upper()}]"
        params = []
        for p in t.params:
            star = "*" if p.required else ""
            default = f"={p.default}" if p.default else ""
            jtype = _JSON_TYPE[p.param_type]
            params.append(f"{p.name}{star}:{jtype}{default}")
        if params:
            lines.append("Params: " + " ".join(params))
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"
