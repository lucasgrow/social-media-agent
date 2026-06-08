"""Deterministic ingest selector — URL pattern decides the tool, no judgement call.

Rule of thumb (why): yt-dlp's Instagram extractor only yields *video* formats, so it
silently returns zero files for image carousels. Those go through Cobalt. Everything
that yt-dlp handles well (reels, YouTube, tweet video) stays on yt-dlp.

    Instagram `/p/` post (image or carousel) → cobalt
    everything else (IG reel/tv, YouTube, X, ...)   → yt_dlp

Use ``fetch(url, output_dir)`` and don't think about which downloader to call.
"""
from pathlib import Path
from urllib.parse import urlparse


def choose_ingestor(url: str) -> str:
    """Return 'cobalt' or 'yt_dlp' for `url`."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    if "instagram.com" in host and "/p/" in path:
        return "cobalt"
    return "yt_dlp"


def fetch(url: str, output_dir: Path) -> dict:
    """Ingest `url` into `output_dir` using the right tool for it.

    Returns the common shape ``{"meta": dict, "media_files": [Path, ...]}``.
    """
    which = choose_ingestor(url)
    if which == "cobalt":
        from social_media_agent.ingest import cobalt

        return cobalt.fetch(url, output_dir)
    from social_media_agent.ingest import yt_dlp

    return yt_dlp.fetch(url, output_dir)
