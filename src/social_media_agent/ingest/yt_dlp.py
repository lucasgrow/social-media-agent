"""yt-dlp ingest adapter — download media + metadata from a URL."""
import json
import shutil
import subprocess
from pathlib import Path


def fetch(url: str, output_dir: Path, timeout: int = 120) -> dict:
    """Download media at url into output_dir using yt-dlp.

    Returns: {"meta": parsed_json_metadata, "media_files": [Path, ...]}
    Raises: RuntimeError if yt-dlp exits non-zero.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    yt_dlp_bin = shutil.which("yt-dlp") or "yt-dlp"
    cmd = [
        yt_dlp_bin,
        url,
        "-o", str(output_dir / "%(id)s.%(ext)s"),
        "--print-json",
        "--no-warnings",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr.strip()}")

    meta = {}
    if result.stdout.strip():
        try:
            meta = json.loads(result.stdout.splitlines()[-1])
        except json.JSONDecodeError:
            meta = {}

    media_files = sorted(
        p for p in output_dir.iterdir()
        if p.is_file() and not p.name.endswith(".json")
    )
    return {"meta": meta, "media_files": media_files}
