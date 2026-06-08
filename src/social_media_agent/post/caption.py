"""Caption skeleton — produce caption.md scaffold per brief context + voice."""
from pathlib import Path

from social_media_agent.brand.brand_loader import parse_design_md, parse_md_with_frontmatter, parse_voice_md


def create_caption_skeleton(post_dir: Path, profile_dir: Path) -> Path:
    """Write a caption.md skeleton based on brief context + profile voice.

    No-op if caption.md already exists.

    Raises:
        FileNotFoundError if brief.md missing.
    """
    out_path = post_dir / "caption.md"
    if out_path.exists():
        return out_path

    brief_path = post_dir / "brief.md"
    if not brief_path.is_file():
        raise FileNotFoundError(f"brief.md not found in {post_dir}")

    brief_meta, _ = parse_md_with_frontmatter(brief_path)
    design_meta, _ = parse_design_md(profile_dir / "brand-kit" / "DESIGN.md")
    voice_meta, _ = parse_voice_md(profile_dir / "VOICE.md")

    context = brief_meta.get("context", "utility")
    ig_handle = design_meta.get("ig_handle", "(no handle)")
    contexts = voice_meta.get("contexts", {}) or {}
    pattern_hint = contexts.get(context, {}).get("pattern", "(no pattern defined)")

    skeleton = f"""# Caption — {brief_meta.get("slug", post_dir.name)}

> **Voice context:** {context}
> **Pattern hint:** {pattern_hint}

```text
(Write the caption here. Follow the pattern hint above.)



{ig_handle}
#hashtag1 #hashtag2
```

## Notes
- (Add any voice/copy decisions here)
"""
    out_path.write_text(skeleton)
    return out_path
