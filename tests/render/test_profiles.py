"""Stage 3: Render profiles tests."""

from biome_mcp.render.profiles import COMPACT, DEFAULT, PROFILES, VERBOSE


def test_default_profile():
    assert DEFAULT.max_chars == 4096
    assert DEFAULT.include_data is True


def test_compact_profile():
    assert COMPACT.max_chars == 1024
    assert COMPACT.include_data is False


def test_verbose_profile():
    assert VERBOSE.max_chars == 16384


def test_profiles_dict():
    assert "default" in PROFILES
    assert "compact" in PROFILES
    assert "verbose" in PROFILES
    assert PROFILES["default"] is DEFAULT
