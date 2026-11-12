"""S1-S2: ErrorCode enum and BiomeError."""

from biome_mcp.errors import BiomeError, ErrorCode


def test_error_code_has_generic_codes():
    codes = {e.value for e in ErrorCode}
    expected = {
        "connection_lost", "command_not_found", "invalid_arguments",
        "timeout", "permission_denied", "internal_error", "cancelled", "unknown",
    }
    assert expected <= codes


def test_biome_error_carries_code_and_message():
    err = BiomeError(ErrorCode.TIMEOUT, "took too long")
    assert err.code is ErrorCode.TIMEOUT
    assert err.message == "took too long"
    assert "timeout" in str(err).lower()
