"""S15-S16: batch_policy decision."""

from biome_mcp.decisions.generated.batch_policy import BatchPolicyInput, batch_policy


def test_batch_policy_read_transient_continues():
    r = batch_policy(BatchPolicyInput(
        cmd_effect="read", error_class="transient", batch_supports_rollback=False,
    ))
    assert r == "continue"


def test_batch_policy_write_permanent_stops():
    r = batch_policy(BatchPolicyInput(
        cmd_effect="write", error_class="permanent", batch_supports_rollback=False,
    ))
    assert r == "stop"


def test_batch_policy_rollback_on_permanent():
    r = batch_policy(BatchPolicyInput(
        cmd_effect="write", error_class="permanent", batch_supports_rollback=True,
    ))
    assert r == "rollback"


def test_batch_policy_default_is_stop():
    r = batch_policy(BatchPolicyInput(
        cmd_effect="read", error_class="unknown", batch_supports_rollback=False,
    ))
    assert r == "stop"
