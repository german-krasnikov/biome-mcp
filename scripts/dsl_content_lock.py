"""Content lock for DSL-generated files.

    python scripts/dsl_content_lock.py generate   write the lock from files on disk
    python scripts/dsl_content_lock.py check       exit 1 when a locked file differs

Adapted from unity-biome-mcp/scripts/dsl_content_lock.py.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = "dsl/content-lock.json"
BANNER = re.compile(
    rb"\A(?:#|//) Generated from [^\n]*\n(?:#|//) source-sha256=[0-9a-f]{64}\r?\n"
)


def digest(root: Path, key: str) -> str | None:
    path = root / key
    if not path.is_file():
        return None
    data = re.sub(rb"\r\n?", b"\n", path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
    return hashlib.sha256(data).hexdigest()


def is_locked(root: Path, name: str) -> bool:
    path = root / name
    if name == LOCK or not path.is_file():
        return False
    if name.startswith("dsl/") and path.suffix != ".md":
        return True
    with path.open("rb") as f:
        return BANNER.match(f.read(400)) is not None


def tracked(root: Path) -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=root, check=True, capture_output=True,
    )
    return listed.stdout.decode("utf-8").split("\0")


def discover(root: Path, names: list[str]) -> list[str]:
    return sorted(name for name in names if is_locked(root, name))


def locked(root: Path = ROOT) -> dict[str, str]:
    return json.loads((root / LOCK).read_text(encoding="utf-8"))["files"]


def stale(root: Path = ROOT) -> list[str]:
    return [
        key for key, want in locked(root).items()
        if (got := digest(root, key)) is None or got != want
    ]


def generate(root: Path, names: list[str]) -> int:
    files = {key: digest(root, key) for key in discover(root, names)}
    if gone := [k for k, v in files.items() if v is None]:
        raise SystemExit(f"cannot lock {gone}: no such file")
    header = "by scripts/dsl_content_lock.py generate; do not edit"
    (root / LOCK).write_text(
        json.dumps({"generated": header, "files": files}, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    return len(files)


def main(argv: list[str]) -> int:
    if argv[1:] == ["generate"]:
        print(f"{LOCK}: {generate(ROOT, tracked(ROOT))} files")
        return 0
    if argv[1:] == ["check"]:
        pinned, bad = locked(), stale()
        for key in bad:
            print(f"stale: {key}", file=sys.stderr)
        print(f"{LOCK}: {len(pinned) - len(bad)} of {len(pinned)} files as locked")
        return 1 if bad else 0
    print("usage: dsl_content_lock.py generate | check", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
