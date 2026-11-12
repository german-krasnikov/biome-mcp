# Generated from dsl/decisions/permission.logic
# source-sha256=202cf751e3fa8e664a43d6570f2af832dff4a6cc4e137a0f7a9c04c2195e44b6
# Edit the source, then run biome generate.

from __future__ import annotations

from dataclasses import dataclass


class LogicInputError(ValueError):
    """An input outside the Logic contract (LOGIC_INPUT_CONTRACT)."""


class ChatPermissionValues:
    ALLOW = "allow"
    DENY_ASK = "denyAsk"
    DENY_DANGEROUS = "denyDangerous"
    DENY_UNKNOWN_MODE = "denyUnknownMode"


@dataclass(frozen=True, slots=True)
class ChatPermissionInput:
    call_dangerous: bool
    call_mutating: bool
    chat_mode: str


def chat_permission(inp: ChatPermissionInput) -> str:
    _check("call.dangerous", inp.call_dangerous, "bool")
    _check("call.mutating", inp.call_mutating, "bool")
    _check("chat.mode", inp.chat_mode, "enum",
           values=("external", "ask", "agent", "fullAccess", "unknown"))
    return _decide_chat_permission(inp)


__all__ = [
    "LogicInputError", "ChatPermissionValues", "ChatPermissionInput",
    "chat_permission",
]


def _check(
    fact_id: str, value: object, kind: str, *,
    values: tuple[str, ...] = (),
) -> None:
    if kind == "bool":
        ok = isinstance(value, bool)
    elif kind == "enum":
        ok = isinstance(value, str) and value in values
    else:
        ok = isinstance(value, str)
    if not ok:
        raise LogicInputError(f"LOGIC_INPUT_CONTRACT: {fact_id}={value!r}")


def _decide_chat_permission(s: ChatPermissionInput) -> str:
    # rule: external (priority 10)
    if s.chat_mode == "external":
        return "allow"
    # rule: unknownMode (priority 11)
    if s.chat_mode == "unknown":
        return "denyUnknownMode"
    # rule: fullAccess (priority 12)
    if s.chat_mode == "fullAccess":
        return "allow"
    # rule: agentDangerous (priority 20)
    if (s.chat_mode == "agent") and (s.call_dangerous is True):
        return "denyDangerous"
    # rule: askBlocked (priority 30)
    if (s.chat_mode == "ask") and (
        (s.call_mutating is True) or (s.call_dangerous is True)
    ):
        return "denyAsk"
    return "allow"
