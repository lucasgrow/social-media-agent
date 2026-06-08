"""Cobalt ingest adapter — downloads social media (incl. IG multi-image carousels).

yt-dlp's Instagram extractor only yields *video* formats, so it returns nothing for
image carousels (the common IG `/p/` post). Cobalt's API handles those: it answers a
`picker` response listing every image/video asset, which this adapter downloads.

Self-contained: talks to a Cobalt API endpoint over HTTP (a local instance by default).
Nothing here depends on any other repo. Returns the same shape as
``ingest.yt_dlp.fetch`` — ``{"meta": dict, "media_files": [Path, ...]}`` — so callers
and the selector can treat both ingestors alike. Files land in ``output_dir`` (pass a
repo-local path, e.g. the post's ``source/`` dir).
"""
import os
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

# Default to a LOCAL Cobalt instance — see docs/usage.md for how to start one.
DEFAULT_API_URL = "http://127.0.0.1:9000/"
_USER_AGENT = "social-media-agent-cobalt/1.0"
_CHUNK = 1024 * 1024
_EXT_BY_KIND = {
    "photo": ".jpg",
    "image": ".jpg",
    "video": ".mp4",
    "gif": ".gif",
    "audio": ".mp3",
    "file": ".bin",
}


class CobaltError(RuntimeError):
    """Raised when the Cobalt API is unreachable or returns an unusable response."""


def _resolve_api_url(explicit: str | None) -> str:
    url = explicit or os.environ.get("COBALT_API_URL") or DEFAULT_API_URL
    return url if url.endswith("/") else url + "/"


def _extension(media_url: str, content_type: str | None, kind: str) -> str:
    suffix = Path(urlparse(media_url).path).suffix
    if suffix and len(suffix) <= 8:
        return suffix
    if content_type:
        import mimetypes

        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed:
            return guessed
    return _EXT_BY_KIND.get(kind, ".bin")


def _unique(path: Path) -> Path:
    if not path.exists():
        return path
    for n in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{n}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise CobaltError(f"Could not create unique path for {path}")


def _download(media_url: str, output_dir: Path, index: int, kind: str, timeout: int) -> Path:
    try:
        resp = requests.get(media_url, headers={"User-Agent": _USER_AGENT}, timeout=timeout, stream=True)
    except requests.RequestException as exc:
        raise CobaltError(f"Download failed for {media_url}: {exc}") from exc
    if resp.status_code != 200:
        raise CobaltError(f"Download failed for {media_url}: HTTP {resp.status_code}")

    suffix = _extension(media_url, resp.headers.get("Content-Type"), kind)
    path = _unique(output_dir / f"{index:02d}-{kind}{suffix}")
    with path.open("wb") as out:
        for chunk in resp.iter_content(_CHUNK):
            if chunk:
                out.write(chunk)
    return path


def _handle(api_url: str, data: dict, output_dir: Path, picker: str, timeout: int) -> list[Path]:
    status = data.get("status")

    if status in {"redirect", "tunnel"}:
        media_url = data.get("url")
        if not media_url:
            raise CobaltError("Cobalt redirect/tunnel response missing 'url'.")
        return [_download(urljoin(api_url, media_url), output_dir, 1, "file", timeout)]

    if status == "picker":
        if picker == "none":
            return []
        items = data.get("picker")
        if not isinstance(items, list):
            raise CobaltError("Cobalt picker response missing 'picker' array.")
        selected = items[:1] if picker == "first" else items
        files: list[Path] = []
        for i, item in enumerate(selected, start=1):
            if not isinstance(item, dict) or not item.get("url"):
                continue
            kind = str(item.get("type") or "file")
            files.append(_download(urljoin(api_url, item["url"]), output_dir, i, kind, timeout))
        return files

    if status == "error":
        raise CobaltError(f"Cobalt error: {data.get('error')}")

    raise CobaltError(f"Unsupported Cobalt status: {status!r}")


def fetch(
    url: str,
    output_dir: Path,
    *,
    api_url: str | None = None,
    api_key: str | None = None,
    picker: str = "all",
    download_mode: str = "auto",
    video_quality: str = "1080",
    timeout: int = 60,
) -> dict:
    """Download `url` via Cobalt into `output_dir`.

    Args:
        url: source post URL (IG `/p/`, `/reel/`, TikTok, etc.).
        output_dir: directory to write assets into (created if missing).
        api_url: Cobalt API base. Defaults to $COBALT_API_URL or the local instance.
        api_key: optional Cobalt API key. Defaults to $COBALT_API_KEY.
        picker: 'all' (every carousel asset), 'first', or 'none'.

    Returns:
        {"meta": <raw Cobalt response>, "media_files": [Path, ...]}.

    Raises:
        CobaltError: API unreachable, bad JSON, or an error/unsupported status.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base = _resolve_api_url(api_url)

    headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": _USER_AGENT}
    key = api_key or os.environ.get("COBALT_API_KEY")
    if key:
        headers["Authorization"] = f"Api-Key {key}"
    payload = {
        "url": url,
        "downloadMode": download_mode,
        "videoQuality": video_quality,
        "filenameStyle": "basic",
    }

    try:
        resp = requests.post(base, json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise CobaltError(
            f"Could not reach Cobalt API at {base}: {exc}. "
            "Start the local instance with `python -m social_media_agent.cobalt ensure`, "
            "or point COBALT_API_URL at a running Cobalt."
        ) from exc
    try:
        data = resp.json()
    except ValueError as exc:
        raise CobaltError("Cobalt API returned invalid JSON.") from exc

    media_files = _handle(base, data, output_dir, picker, timeout)
    return {"meta": data, "media_files": media_files}
