"""Stage 2 (optional) — Serper.dev image search for candidate reference URLs.

Tertiary acquisition source: user-provided photos come first, then the agent's own
web search (Chrome MCP, conversational), then Serper if a key is configured. Absent
key → serper_available() is False and the caller simply skips this path.
"""
import os

import requests

SERPER_IMAGES_URL = "https://google.serper.dev/images"


def serper_key() -> str | None:
    """SERPER_API_KEY from env, or None if unset/empty."""
    return os.environ.get("SERPER_API_KEY") or None


def serper_available() -> bool:
    return serper_key() is not None


def serper_image_search(
    query: str, n: int = 5, api_key: str | None = None, timeout: int = 30
) -> list[str]:
    """Return up to `n` candidate image URLs for `query`.

    Raises RuntimeError if no API key is available (caller should gate on
    serper_available()).
    """
    key = api_key or serper_key()
    if not key:
        raise RuntimeError("SERPER_API_KEY not set — Serper search unavailable")

    response = requests.post(
        SERPER_IMAGES_URL,
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
        json={"q": query, "num": n},
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    urls = [img["imageUrl"] for img in data.get("images", []) if img.get("imageUrl")]
    return urls[:n]
