"""Versionorder decision — semver comparison."""

from biome_mcp.decisions.generated.versionorder import IsNewerInput, is_newer


def test_equal_not_newer():
    assert is_newer(IsNewerInput(
        ver_parsed=True, ver_cand_pre=False, ver_cur_pre=False, ver_triple="equal",
    )) is False


def test_greater_is_newer():
    assert is_newer(IsNewerInput(
        ver_parsed=True, ver_cand_pre=False, ver_cur_pre=False, ver_triple="greater",
    )) is True


def test_less_is_not_newer():
    assert is_newer(IsNewerInput(
        ver_parsed=True, ver_cand_pre=False, ver_cur_pre=False, ver_triple="less",
    )) is False


def test_rc_never_shown_to_stable_user():
    assert is_newer(IsNewerInput(
        ver_parsed=True, ver_cand_pre=True, ver_cur_pre=False, ver_triple="greater",
    )) is False


def test_release_over_its_rc():
    assert is_newer(IsNewerInput(
        ver_parsed=True, ver_cand_pre=False, ver_cur_pre=True, ver_triple="equal",
    )) is True


def test_unparsed_is_not_newer():
    assert is_newer(IsNewerInput(
        ver_parsed=False, ver_cand_pre=False, ver_cur_pre=False, ver_triple="greater",
    )) is False
