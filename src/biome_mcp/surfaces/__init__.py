"""Generated module surfaces — DO NOT EDIT."""
# framing-sha256=3cfc91ffa1ce151cf0098ed75855e5e95367f0292122adeebb577b507e46b8cd
# lockfile-sha256=60a1b315bbbc2330bae39ce3007a0b37c919cf39003a29bb59a3cb81dcc054d2

FRAMING_SURFACE: frozenset[str] = frozenset({
    "MAX_FRAME_BYTES",
    "apply_socket_options",
    "frame_read",
    "frame_read_with_timeout",
    "frame_write",
})
LOCKFILE_SURFACE: frozenset[str] = frozenset({
    "acquire_lock",
    "is_pid_alive",
    "read_lock_metadata",
    "release_lock",
    "write_lock_metadata",
})
