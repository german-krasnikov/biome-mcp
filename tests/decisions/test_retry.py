"""S13-S14: retry decision."""

from biome_mcp.decisions.generated.retry import RetryGateInput, retry_gate


def test_retry_connection_lost_is_retryable():
    r = retry_gate(RetryGateInput(
        retry_error_code="connection_lost", retry_attempt=0, retry_max_retries=3,
    ))
    assert r == "retry"


def test_retry_timeout_is_retryable():
    r = retry_gate(RetryGateInput(
        retry_error_code="timeout", retry_attempt=0, retry_max_retries=3,
    ))
    assert r == "retry"


def test_retry_invalid_args_not_retryable():
    r = retry_gate(RetryGateInput(
        retry_error_code="invalid_arguments", retry_attempt=0, retry_max_retries=3,
    ))
    assert r == "fail"


def test_retry_max_retries_reached():
    r = retry_gate(RetryGateInput(
        retry_error_code="connection_lost", retry_attempt=3, retry_max_retries=3,
    ))
    assert r == "max_retries"
