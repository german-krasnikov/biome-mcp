"""Permission decision — effect-based permission ladder."""

import pytest

from biome_mcp.decisions.generated.permission import (
    LogicInputError,
    RequiredPermissionInput,
    required_permission,
)


def test_read_requires_read():
    assert required_permission(RequiredPermissionInput(cmd_effect="read")) == "read"


def test_write_requires_write():
    assert required_permission(RequiredPermissionInput(cmd_effect="write")) == "write"


def test_idempotent_write_requires_write():
    assert required_permission(RequiredPermissionInput(cmd_effect="idempotent_write")) == "write"


def test_bad_effect_raises():
    with pytest.raises(LogicInputError, match="LOGIC_INPUT_CONTRACT"):
        required_permission(RequiredPermissionInput(cmd_effect="admin"))
