"""S17-S18: error_class decision."""

import pytest

from biome_mcp.decisions.generated.error_class import (
    ErrorClassInput,
    LogicInputError,
    error_class,
)


def test_error_class_timeout_is_transient():
    assert error_class(ErrorClassInput(error_code="timeout")) == "transient"


def test_error_class_connection_lost_is_transient():
    assert error_class(ErrorClassInput(error_code="connection_lost")) == "transient"


def test_error_class_invalid_args_is_permanent():
    assert error_class(ErrorClassInput(error_code="invalid_arguments")) == "permanent"


def test_error_class_permission_denied_is_permanent():
    assert error_class(ErrorClassInput(error_code="permission_denied")) == "permanent"


def test_error_class_internal_is_unknown():
    assert error_class(ErrorClassInput(error_code="internal_error")) == "unknown"


def test_error_class_bad_code_raises():
    with pytest.raises(LogicInputError, match="LOGIC_INPUT_CONTRACT"):
        error_class(ErrorClassInput(error_code="nonexistent"))
