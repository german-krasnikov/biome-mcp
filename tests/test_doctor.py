"""Stage 3: Doctor diagnostic tests."""

import pytest

from biome_mcp.doctor import Doctor


@pytest.mark.asyncio
async def test_doctor_all_pass():
    async def ok_check():
        return True

    doc = Doctor()
    doc.add_check("conn", ok_check)
    report = await doc.run()
    assert report.all_passed
    assert "1/1" in report.summary()


@pytest.mark.asyncio
async def test_doctor_failure():
    async def fail_check():
        raise RuntimeError("broken")

    doc = Doctor()
    doc.add_check("bad", fail_check)
    report = await doc.run()
    assert not report.all_passed
    assert "broken" in report.checks[0].message
