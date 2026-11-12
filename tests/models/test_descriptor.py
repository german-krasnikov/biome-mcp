"""S3-S6: CommandEffect, ParamSpec, CommandDescriptor."""

import pytest

from biome_mcp.models.descriptor import CommandDescriptor, CommandEffect, ParamSpec


def test_command_effect_enum_values():
    assert CommandEffect.READ == "read"
    assert CommandEffect.WRITE == "write"
    assert CommandEffect.IDEMPOTENT_WRITE == "idempotent_write"


def test_param_spec_required_defaults():
    p = ParamSpec(name="path", type=str)
    assert p.required is True
    assert p.default is None


def test_descriptor_is_frozen():
    d = CommandDescriptor(
        name="scene.inspect", namespace="scene", summary="Inspect scene",
        params=(),
    )
    with pytest.raises(AttributeError):
        d.name = "other"  # type: ignore[misc]


def test_descriptor_batchable_default_true():
    d = CommandDescriptor(
        name="scene.inspect", namespace="scene", summary="Inspect",
        params=(),
    )
    assert d.batchable is True
    assert d.effect is CommandEffect.READ
    assert d.requires == frozenset()
