"""Env helpers — .env loader + repo root walk-up finder."""
import os
from pathlib import Path


def load_env(env_path: Path, inject: bool = False) -> dict:
    """Parse a .env file (KEY=VALUE per line).

    Naive parser — does NOT handle escape sequences (`\\n`, `\\\\`) or
    multi-line values. For complex .env files, use python-dotenv.

    Args:
        env_path: path to .env file (may not exist)
        inject: if True, also set os.environ.setdefault(key, value) for each entry
                (does NOT override values already in the environment)

    Returns:
        dict of parsed KEY → VALUE strings. Empty dict if file missing.
    """
    result: dict[str, str] = {}
    if not env_path.is_file():
        return result
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        result[key] = value
        if inject:
            os.environ.setdefault(key, value)
    return result


def find_repo_root(start: Path) -> Path:
    """Walk up from `start` looking for pyproject.toml. Return its parent dir.

    Raises:
        FileNotFoundError if pyproject.toml not found in any ancestor.
    """
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in [cur, *cur.parents]:
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise FileNotFoundError(f"pyproject.toml not found walking up from {start}")
