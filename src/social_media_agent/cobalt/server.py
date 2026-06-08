"""Provision a LOCAL Cobalt API from source — cross-platform (Windows/macOS/Linux).

Why this exists: yt-dlp's Instagram extractor only yields video formats, so it returns
nothing for image carousels. Cobalt handles those. To stay self-contained (no dependency
on any other repo or hosted service), the project provisions its OWN local Cobalt:

    clone the official cobalt repo  →  pnpm install  →  start the API on 127.0.0.1:9000

Everything lives under a project-local cache dir (``$COBALT_HOME`` or ``<repo>/.cobalt``,
gitignored). Driven by ``python -m social_media_agent.cobalt`` (works on every OS that has
Python) and wired into ``install.sh``.

Requires Node.js + pnpm on PATH. If missing, raises with per-OS install hints — we do not
silently fall back, so "setup said ready" actually means ready.
"""
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from social_media_agent.utils.env import find_repo_root

COBALT_REPO = "https://github.com/imputnet/cobalt"
DEFAULT_API_URL = "http://127.0.0.1:9000/"
# Native deps that must be rebuilt when the Node ABI changes (cobalt uses isolated-vm).
_NATIVE_DEPS = ["isolated-vm", "syscall-napi"]


class CobaltSetupError(RuntimeError):
    """Provisioning failed (missing toolchain, clone/install error, never came up)."""


# ---------------------------------------------------------------- paths / config


def api_url() -> str:
    url = os.environ.get("COBALT_API_URL") or DEFAULT_API_URL
    return url if url.endswith("/") else url + "/"


def cobalt_home() -> Path:
    explicit = os.environ.get("COBALT_HOME")
    if explicit:
        return Path(explicit).expanduser()
    try:
        root = find_repo_root(Path.cwd())
    except FileNotFoundError:
        root = Path.cwd()
    return root / ".cobalt"


def _src_dir(home: Path) -> Path:
    return home / "cobalt-src"


def _pid_file(home: Path) -> Path:
    return home / "cobalt.pid"


def _log_file(home: Path) -> Path:
    return home / "cobalt.log"


# ---------------------------------------------------------------- health check


def is_running(url: str | None = None, timeout: float = 2.0) -> bool:
    """True if a Cobalt API answers at `url` (defaults to the configured api_url)."""
    target = url or api_url()
    try:
        req = urllib.request.Request(target, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return False
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return isinstance(data, dict) and "cobalt" in data
    except (urllib.error.URLError, OSError, json.JSONDecodeError, ValueError):
        return False


# ---------------------------------------------------------------- toolchain


def _install_hint(tool: str) -> str:
    system = platform.system()
    hints = {
        "node": {
            "Darwin": "brew install node",
            "Linux": "use your distro package manager or https://nodejs.org",
            "Windows": "winget install OpenJS.NodeJS  (or https://nodejs.org)",
        },
        "pnpm": {
            "Darwin": "corepack enable && corepack prepare pnpm@latest --activate",
            "Linux": "corepack enable && corepack prepare pnpm@latest --activate",
            "Windows": "corepack enable && corepack prepare pnpm@latest --activate",
        },
    }
    return hints.get(tool, {}).get(system, f"install {tool} and put it on PATH")


def _require(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise CobaltSetupError(f"'{tool}' not found on PATH. Install it: {_install_hint(tool)}")
    return path


def _run(cmd: list[str], cwd: Path, label: str) -> None:
    result = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-2000:]
        raise CobaltSetupError(f"{label} failed (exit {result.returncode}):\n{detail}")


# ---------------------------------------------------------------- source / build


def _ensure_source(home: Path) -> Path:
    """Clone cobalt (shallow) and install deps. Rebuild native deps on Node ABI change."""
    home.mkdir(parents=True, exist_ok=True)
    src = _src_dir(home)
    git = _require("git")
    node = _require("node")
    pnpm = _require("pnpm")

    if not (src / ".git").is_dir():
        _run([git, "clone", "--depth", "1", COBALT_REPO, str(src)], home, "git clone cobalt")

    node_abi = subprocess.run([node, "-p", "process.versions.modules"], capture_output=True, text=True).stdout.strip()
    abi_stamp = src / ".sma-node-abi"

    if not (src / "node_modules").is_dir():
        _run([pnpm, "install"], src, "pnpm install")
        abi_stamp.write_text(node_abi + "\n")
    elif not abi_stamp.is_file() or abi_stamp.read_text().strip() != node_abi:
        _run([pnpm, "--filter", "@imput/cobalt-api", "rebuild", *_NATIVE_DEPS], src, "pnpm rebuild native deps")
        abi_stamp.write_text(node_abi + "\n")

    return src


# ---------------------------------------------------------------- start / stop


def start(home: Path | None = None, url: str | None = None, wait: float = 90.0) -> int:
    """Provision (if needed) and start the local Cobalt API detached. Returns its PID.

    Idempotent: if one is already answering, returns 0 without starting another.
    """
    target = url or api_url()
    if is_running(target):
        return 0

    home = home or cobalt_home()
    src = _ensure_source(home)
    pnpm = _require("pnpm")

    env = dict(os.environ)
    env["API_URL"] = target
    env.setdefault("API_LISTEN_ADDRESS", "127.0.0.1")

    log = _log_file(home).open("ab")
    creation = {}
    if os.name == "nt":
        creation["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    else:
        creation["start_new_session"] = True

    proc = subprocess.Popen(
        [pnpm, "--filter", "@imput/cobalt-api", "start"],
        cwd=str(src),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        **creation,
    )
    _pid_file(home).write_text(str(proc.pid))

    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            tail = _log_file(home).read_text(errors="replace")[-2000:]
            raise CobaltSetupError(f"Cobalt exited during startup (code {proc.returncode}):\n{tail}")
        if is_running(target):
            return proc.pid
        time.sleep(1.5)

    raise CobaltSetupError(f"Cobalt did not become reachable at {target} within {wait:.0f}s. See {_log_file(home)}")


def ensure(home: Path | None = None, url: str | None = None) -> bool:
    """Guarantee a local Cobalt is running. Returns True if it was already up."""
    target = url or api_url()
    if is_running(target):
        return True
    start(home=home, url=target)
    return False


def stop(home: Path | None = None) -> bool:
    """Stop the Cobalt we started (via its pid file). Returns True if a process was signalled."""
    home = home or cobalt_home()
    pid_file = _pid_file(home)
    if not pid_file.is_file():
        return False
    try:
        pid = int(pid_file.read_text().strip())
    except ValueError:
        pid_file.unlink(missing_ok=True)
        return False
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
        else:
            os.killpg(os.getpgid(pid), 15)
    except (ProcessLookupError, PermissionError, OSError):
        pid_file.unlink(missing_ok=True)
        return False
    pid_file.unlink(missing_ok=True)
    return True


def status(url: str | None = None) -> dict:
    target = url or api_url()
    return {"api_url": target, "running": is_running(target), "home": str(cobalt_home())}


def _print(msg: str) -> None:
    print(msg, file=sys.stderr)
