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
