"""Grounded-ref bookkeeping — persist validated refs into the post + a manifest.

Layout (shared across versions, lives at the post root):
    <post_dir>/refs/grounded/
        grounding.json            # manifest: one entry per registered ref
        <subject-slug>/<file>     # the ref image bytes
"""
import json
import shutil
from pathlib import Path

from social_media_agent.post.slug import auto_slug

GROUNDED_SUBDIR = Path("refs") / "grounded"
MANIFEST_NAME = "grounding.json"
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def grounded_dir(post_dir: Path) -> Path:
    return post_dir / GROUNDED_SUBDIR


def subject_slug(name: str) -> str:
    return auto_slug(title=name)


def _manifest_path(post_dir: Path) -> Path:
    return grounded_dir(post_dir) / MANIFEST_NAME


def _load_manifest(post_dir: Path) -> list[dict]:
    path = _manifest_path(post_dir)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def register_ref(
    post_dir: Path,
    subject: dict,
    image_path: Path,
    source: str,
    score: float | None = None,
) -> Path:
    """Copy `image_path` into the post's grounded refs and append a manifest entry.

    `source` ∈ {"user", "web", "serper"}. Returns the saved ref path. Filenames are
    de-duplicated per subject so multiple refs for one subject coexist.
    """
    slug = subject_slug(subject.get("name", "subject"))
    dest_dir = grounded_dir(post_dir) / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = image_path.suffix.lower() if image_path.suffix.lower() in IMAGE_EXTS else ".png"
    n = sum(1 for _ in dest_dir.glob(f"{slug}-*")) + 1
    dest = dest_dir / f"{slug}-{n}{ext}"
    shutil.copy2(image_path, dest)

    manifest = _load_manifest(post_dir)
    manifest.append(
        {
            "subject": subject.get("name", ""),
            "kind": subject.get("kind", "other"),
            "file": str(dest.relative_to(post_dir)),
            "source": source,
            "score": score,
            "search_query": subject.get("search_query", ""),
            "why": subject.get("why", ""),
        }
    )
    _manifest_path(post_dir).write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return dest


def collect_grounded_refs(post_dir: Path) -> list[Path]:
    """All grounded ref image paths under the post (sorted, manifest excluded)."""
    base = grounded_dir(post_dir)
    if not base.is_dir():
        return []
    return sorted(
        p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )
