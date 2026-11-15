"""Parse TOOL blocks from .biome source text."""
from __future__ import annotations

import shlex
from dataclasses import dataclass, field


@dataclass
class ParamDecl:
    name: str
    param_type: str
    required: bool = False
    default: str | None = None
    description: str = ""


@dataclass
class ToolDecl:
    name: str
    summary: str
    effect: str = "read"
    batchable: bool = False
    blast_radius: int = 0
    params: list[ParamDecl] = field(default_factory=list)

    @property
    def namespace(self) -> str:
        return self.name.split(".")[0] if "." in self.name else self.name


_EFFECTS = {"read", "write", "idempotent_write"}
_TYPES = {"str", "int", "float", "bool", "list"}


def parse_tools(source: str) -> list[ToolDecl]:
    tools: list[ToolDecl] = []
    current: ToolDecl | None = None

    for lineno, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("TOOL "):
            if current is not None:
                msg = f"line {lineno}: nested TOOL (missing END?)"
                raise SyntaxError(msg)
            current = _parse_tool_head(line, lineno)
            continue

        if line == "END":
            if current is None:
                msg = f"line {lineno}: END without TOOL"
                raise SyntaxError(msg)
            tools.append(current)
            current = None
            continue

        if line.startswith("PARAM ") and current is not None:
            current.params.append(_parse_param(line, lineno))
            continue

    if current is not None:
        msg = "unexpected EOF: TOOL without END"
        raise SyntaxError(msg)

    return tools


def _parse_tool_head(line: str, lineno: int) -> ToolDecl:
    tokens = shlex.split(line)
    if len(tokens) < 4:
        msg = f"line {lineno}: TOOL requires name, summary, effect"
        raise SyntaxError(msg)

    name = tokens[1]
    summary = tokens[2]
    effect = tokens[3]
    if effect not in _EFFECTS:
        msg = f"line {lineno}: unknown effect '{effect}', expected {_EFFECTS}"
        raise SyntaxError(msg)

    batchable = "BATCHABLE" in tokens[4:]
    blast = 0
    rest = tokens[4:]
    for i, t in enumerate(rest):
        if t == "BLAST" and i + 1 < len(rest):
            try:
                blast = int(rest[i + 1])
            except ValueError:
                msg = f"line {lineno}: BLAST requires an integer, got '{rest[i + 1]}'"
                raise SyntaxError(msg) from None

    return ToolDecl(
        name=name, summary=summary, effect=effect,
        batchable=batchable, blast_radius=blast,
    )


def _parse_param(line: str, lineno: int) -> ParamDecl:
    tokens = shlex.split(line)
    idx = 1
    if idx >= len(tokens):
        msg = f"line {lineno}: PARAM requires a name"
        raise SyntaxError(msg)

    pname = tokens[idx]
    idx += 1

    required = False
    if idx < len(tokens) and tokens[idx] == "REQUIRED":
        required = True
        idx += 1

    if idx >= len(tokens):
        msg = f"line {lineno}: PARAM '{pname}' requires a type"
        raise SyntaxError(msg)

    ptype = tokens[idx]
    if ptype not in _TYPES:
        msg = f"line {lineno}: unknown type '{ptype}', expected {_TYPES}"
        raise SyntaxError(msg)
    idx += 1

    default = None
    if idx < len(tokens) and tokens[idx] == "DEFAULT":
        idx += 1
        if idx >= len(tokens):
            msg = f"line {lineno}: DEFAULT requires a value"
            raise SyntaxError(msg)
        default = tokens[idx]
        idx += 1
        _validate_default(ptype, default, pname, lineno)

    description = tokens[idx] if idx < len(tokens) else ""
    return ParamDecl(
        name=pname, param_type=ptype, required=required,
        default=default, description=description,
    )


def _validate_default(ptype: str, default: str, pname: str, lineno: int) -> None:
    loc = f"line {lineno}: DEFAULT for {ptype} param '{pname}'"
    if ptype == "int":
        try:
            int(default)
        except ValueError:
            raise SyntaxError(f"{loc} must be integer, got '{default}'") from None
    elif ptype == "float":
        try:
            float(default)
        except ValueError:
            raise SyntaxError(f"{loc} must be number, got '{default}'") from None
    elif ptype == "bool":
        if default.lower() not in ("true", "false", "yes", "no"):
            msg = f"{loc} must be true/false, got '{default}'"
            raise SyntaxError(msg)
    elif ptype == "list":
        raise SyntaxError(f"line {lineno}: DEFAULT not supported for list param '{pname}'")
