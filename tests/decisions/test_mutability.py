"""S11-S12: mutability decision — engine-agnostic, based on CommandEffect."""

import pytest

from biome_mcp.decisions.generated.mutability import (
    IsMutatingInput,
    LogicInputError,
    is_mutating,
)


def test_mutability_write_is_mutating():
    assert is_mutating(IsMutatingInput(cmd_effect="write")) is True


def test_mutability_read_is_not_mutating():
    assert is_mutating(IsMutatingInput(cmd_effect="read")) is False


def test_mutability_idempotent_write_is_mutating():
    assert is_mutating(IsMutatingInput(cmd_effect="idempotent_write")) is True


def test_mutability_bad_effect_raises():
    with pytest.raises(LogicInputError, match="LOGIC_INPUT_CONTRACT"):
        is_mutating(IsMutatingInput(cmd_effect="delete"))
