"""Brand loader — parse DESIGN.md, VOICE.md, list brand-kit/pages assets."""
from pathlib import Path

import yaml


def parse_md_with_frontmatter(path: Path) -> tuple[dict, str]:
    """Parse a markdown file with optional YAML frontmatter.

    Returns (meta_dict, body_str). If no frontmatter, returns ({}, full_content).
    Raises FileNotFoundError if file missing.
    """
    text = path.read_text()
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return meta, body


def parse_design_md(path: Path) -> tuple[dict, str]:
    """Parse a DESIGN.md (YAML frontmatter + markdown body)."""
    return parse_md_with_frontmatter(path)


def parse_voice_md(path: Path) -> tuple[dict, str]:
    """Parse a VOICE.md (YAML frontmatter + markdown body)."""
    return parse_md_with_frontmatter(path)


def list_brand_pages(pages_dir: Path) -> list[Path]:
    """Return sorted image paths in brand-kit/pages/ (png/jpg/jpeg/webp).

    Brand pages may be photographs (jpg), not just exported PNGs — accept the common
    raster formats so a profile's reference imagery is actually picked up.
    """
    if not pages_dir.is_dir():
        raise FileNotFoundError(f"brand-kit pages dir not found: {pages_dir}")
    exts = (".png", ".jpg", ".jpeg", ".webp")
    return sorted(p for p in pages_dir.iterdir() if p.is_file() and p.suffix.lower() in exts)
