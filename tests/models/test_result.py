"""S7-S10: CommandResult and CommandStatus."""

from biome_mcp.models.result import CommandResult, CommandStatus


def test_result_ok_status():
    r = CommandResult(status=CommandStatus.OK, text="done")
    assert r.status is CommandStatus.OK
    assert r.text == "done"
    assert r.complete is True
    assert r.error_code is None


def test_result_error_carries_code():
    r = CommandResult(
        status=CommandStatus.FAILED, text="boom", error_code="E_INTERNAL",
    )
    assert r.error_code == "E_INTERNAL"


def test_result_factory_ok():
    r = CommandResult.ok("all good", data={"count": 3})
    assert r.status is CommandStatus.OK
    assert r.text == "all good"
    assert r.data == {"count": 3}


def test_result_factory_error():
    r = CommandResult.error("E_TIMEOUT", "timed out")
    assert r.status is CommandStatus.FAILED
    assert r.error_code == "E_TIMEOUT"
    assert r.text == "timed out"


def test_result_factory_cancelled():
    r = CommandResult.cancelled("user abort")
    assert r.status is CommandStatus.CANCELLED
    assert r.text == "user abort"


def test_result_factory_timed_out():
    r = CommandResult.timed_out("took too long")
    assert r.status is CommandStatus.TIMED_OUT
    assert r.text == "took too long"


def test_result_from_raw_ok_with_string_data():
    r = CommandResult.from_raw({"ok": True, "data": "hierarchy text"})
    assert r.status is CommandStatus.OK
    assert r.text == "hierarchy text"
    assert r.data == "hierarchy text"


def test_result_from_raw_ok_with_structured_data():
    r = CommandResult.from_raw({"ok": True, "data": {"count": 3}})
    assert r.status is CommandStatus.OK
    assert r.data == {"count": 3}


def test_result_from_raw_ok_missing_data_defaults_empty():
    r = CommandResult.from_raw({"ok": True})
    assert r.status is CommandStatus.OK
    assert r.text == ""
    assert r.data == ""


def test_result_from_raw_error_carries_message():
    r = CommandResult.from_raw({"ok": False, "err": "connection lost"})
    assert r.status is CommandStatus.FAILED
    assert r.text == "connection lost"
    assert r.error_code == "E_RAW"


def test_result_from_raw_error_missing_err_defaults_unknown():
    r = CommandResult.from_raw({"ok": False})
    assert r.status is CommandStatus.FAILED
    assert r.text == "unknown"
