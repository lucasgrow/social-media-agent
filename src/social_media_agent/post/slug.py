"""Auto-slug generation from title/URL."""
import re
import unicodedata
from urllib.parse import urlparse


MAX_SLUG_LEN = 60


def _slugify(text: str) -> str:
    """Lowercase, strip accents, replace non-alnum with single dash, trim."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    lowered = normalized.lower()
    dashed = re.sub(r"[^a-z0-9]+", "-", lowered)
    trimmed = dashed.strip("-")
    if len(trimmed) > MAX_SLUG_LEN:
        trimmed = trimmed[:MAX_SLUG_LEN].rstrip("-")
    return trimmed


def auto_slug(title: str | None = None, url: str | None = None) -> str:
    """Auto-generate a URL-safe slug from title (preferred), URL path, or 'post' fallback."""
    if title and title.strip():
        slug = _slugify(title)
        if slug:
            return slug
    if url:
        path = urlparse(url).path
        last_segment = [seg for seg in path.split("/") if seg]
        if last_segment:
            slug = _slugify(last_segment[-1])
            if slug:
                return slug
    return "post"
