"""Permission decision — ladder from chat modes."""

from biome_mcp.decisions.generated.permission import ChatPermissionInput, chat_permission


def test_external_allows():
    r = chat_permission(ChatPermissionInput(
        chat_mode="external", call_mutating=False, call_dangerous=False,
    ))
    assert r == "allow"


def test_unknown_mode_denies():
    r = chat_permission(ChatPermissionInput(
        chat_mode="unknown", call_mutating=False, call_dangerous=False,
    ))
    assert r == "denyUnknownMode"


def test_full_access_allows_everything():
    r = chat_permission(ChatPermissionInput(
        chat_mode="fullAccess", call_mutating=True, call_dangerous=True,
    ))
    assert r == "allow"


def test_agent_dangerous_denies():
    r = chat_permission(ChatPermissionInput(
        chat_mode="agent", call_mutating=False, call_dangerous=True,
    ))
    assert r == "denyDangerous"


def test_ask_mutating_denies():
    r = chat_permission(ChatPermissionInput(
        chat_mode="ask", call_mutating=True, call_dangerous=False,
    ))
    assert r == "denyAsk"
