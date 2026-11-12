"""Stage 2: Registry tests — metadata store only."""

import pytest

from biome_mcp.errors import BiomeError, ErrorCode
from biome_mcp.models.descriptor import CommandDescriptor, CommandEffect
from biome_mcp.registry import Registry


def _desc(name: str, ns: str = "test", effect: CommandEffect = CommandEffect.READ):
    return CommandDescriptor(name=name, namespace=ns, summary=name, params=())


def test_register_and_get():
    reg = Registry()
    desc = _desc("test.hello")
    reg.register(desc)
    assert reg.get("test.hello") is desc


def test_unknown_command_raises():
    reg = Registry()
    with pytest.raises(BiomeError) as exc_info:
        reg.get("nonexistent")
    assert exc_info.value.code == ErrorCode.COMMAND_NOT_FOUND


def test_duplicate_raises():
    reg = Registry()
    reg.register(_desc("test.hello"))
    with pytest.raises(BiomeError) as exc_info:
        reg.register(_desc("test.hello"))
    assert exc_info.value.code == ErrorCode.INVALID_ARGUMENTS


def test_names_filter_namespace():
    reg = Registry()
    reg.register(_desc("scene.inspect", ns="scene"))
    reg.register(_desc("scene.create", ns="scene"))
    reg.register(_desc("file.read", ns="file"))
    assert reg.names() == ("file.read", "scene.create", "scene.inspect")
    assert reg.names("scene") == ("scene.create", "scene.inspect")
    assert reg.names("file") == ("file.read",)
    assert reg.names("missing") == ()


def test_descriptors():
    reg = Registry()
    d1, d2 = _desc("a.one"), _desc("b.two")
    reg.register(d1)
    reg.register(d2)
    assert set(reg.descriptors()) == {d1, d2}
