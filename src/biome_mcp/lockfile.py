"""Platform-agnostic PID lockfile primitives — acquire, release, metadata I/O.

lock_dir is always caller-supplied. No engine-specific directory defaults here.
Lockfile naming: server-{port}-{pid}.lock
Line 1: PID. Line 2 (optional): JSON metadata (e.g. {"ppid": N}).
"""
import contextlib
import json
import os
import sys
from pathlib import Path

_IS_WIN = sys.platform == "win32"

# Lock sentinel byte lives at offset 1024 — far outside PID data (bytes 0-31).
# On Windows, mandatory locking blocks reads on locked bytes, so the lock region
# MUST NOT overlap PID data that other processes need to read.
_LOCK_OFFSET = 1024

_OPEN_FLAGS = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)

# Maps fd → lock file path for cleanup in release_lock
_lock_paths: dict[int, str] = {}


if _IS_WIN:
    import msvcrt

    def _lock_nb(fd: int) -> None:
        """Non-blocking exclusive lock on sentinel byte at offset 1024."""
        os.lseek(fd, _LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)

    def _unlock(fd: int) -> None:
        """Release the sentinel byte lock."""
        os.lseek(fd, _LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _lock_nb(fd: int) -> None:
        """Non-blocking exclusive flock (advisory, whole-file)."""
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)


def is_pid_alive(pid: int | None) -> bool:
    """Return True if the process with given PID exists."""
    if pid is None:
        return False
    if sys.platform == "win32":
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True  # alive but no permission (cross-user on Unix)
    except (OSError, ProcessLookupError):
        return False


def _write_pid(fd: int) -> None:
    """Write current PID to bytes 0-31 of the lockfile."""
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    os.write(fd, f"{os.getpid()}\n".encode())


def write_lock_metadata(fd: int, metadata: dict) -> None:
    """Append JSON metadata on line 2 of the lockfile (after the PID line)."""
    os.lseek(fd, 0, os.SEEK_SET)
    pid_data = os.read(fd, 64).decode(errors="ignore")
    pid_end = pid_data.find("\n")
    if pid_end < 0:
        pid_end = len(pid_data)
    meta_start = pid_end + 1
    os.lseek(fd, meta_start, os.SEEK_SET)
    payload = (json.dumps(metadata, ensure_ascii=False) + "\n").encode()
    os.write(fd, payload)
    os.ftruncate(fd, meta_start + len(payload))


def read_lock_metadata(fd: int) -> dict | None:
    """Read JSON metadata from line 2 of the lockfile. Returns None if absent/corrupt."""
    os.lseek(fd, 0, os.SEEK_SET)
    data = os.read(fd, 1024).decode(errors="ignore")
    lines = data.split("\n")
    if len(lines) < 2 or not lines[1].strip():
        return None
    try:
        return json.loads(lines[1])
    except json.JSONDecodeError:
        return None


def _read_pid_from_fd(fd: int) -> int | None:
    """Read PID from bytes 0-31. Always readable — outside the locked region."""
    os.lseek(fd, 0, os.SEEK_SET)
    data = os.read(fd, 32).decode(errors="ignore").strip()
    try:
        return int(data)
    except ValueError:
        return None


def acquire_lock(lock_dir: Path | str, port: int, metadata: dict | None = None) -> int:
    """Create a per-PID presence file and take exclusive flock on it.

    Each session uses server-{port}-{pid}.lock — multiple sessions coexist.
    Raises RuntimeError if this PID already holds the lock (rapid restart race).
    metadata: optional dict written as JSON on line 2 via write_lock_metadata.
    """
    lock_dir = Path(lock_dir)
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = lock_dir / f"server-{port}-{os.getpid()}.lock"

    fd = os.open(str(lock_file), _OPEN_FLAGS, 0o600)
    try:
        _lock_nb(fd)
    except (BlockingIOError, OSError):
        os.close(fd)
        raise RuntimeError(
            f"Cannot acquire exclusive lock for port {port} (PID {os.getpid()} already holds it)"
        ) from None

    _write_pid(fd)
    write_lock_metadata(fd, {"ppid": os.getppid()})
    if metadata is not None:
        write_lock_metadata(fd, metadata)
    _lock_paths[fd] = str(lock_file)
    return fd


def release_lock(fd: int) -> None:
    """Unlock, unlink the presence file, and close the fd."""
    with contextlib.suppress(OSError):
        _unlock(fd)
    path = _lock_paths.pop(fd, None)
    close_error: OSError | None = None
    try:
        os.close(fd)
    except OSError as exc:
        close_error = exc
    if path:
        with contextlib.suppress(OSError):
            os.unlink(path)
    if close_error is not None:
        raise close_error
