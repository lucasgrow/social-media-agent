"""Materialize craft.py into a post folder from brief.md + the package template."""
from pathlib import Path

from social_media_agent.brand.brand_loader import parse_md_with_frontmatter
from social_media_agent.engines.spec import FORMAT_TO_SIZE  # canonical openai sizes

# Default template ships inside the package (src/social_media_agent/templates/).
DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

DEFAULT_ENGINE = "openai_gpt_image_2"

FORMAT_TO_FILENAME = {
    "feed_1x1": "feed.png",
    "feed_4x5": "feed.png",
    "carousel_4x5": "carousel.png",
    "story_9x16_still": "story.png",
    "reel_9x16": "reel.mp4",
    "story_video_9x16": "story.mp4",
}


def materialize_craft_py(post_dir: Path, template_dir: Path | None = None) -> Path:
    """Materialize craft.py into post_dir using the package template + brief.md slots.

    Args:
        post_dir: the posts/YYYY-MM/NN-slug/ directory
        template_dir: directory holding craft.py.tmpl. Defaults to the template
            shipped inside the social_media_agent package.

    Returns:
        Path to the materialized craft.py.

    Raises:
        FileNotFoundError if brief.md or craft.py.tmpl missing.
    """
    if template_dir is None:
        template_dir = DEFAULT_TEMPLATE_DIR

    brief_path = post_dir / "brief.md"
    if not brief_path.is_file():
        raise FileNotFoundError(f"brief.md not found in {post_dir}")

    brief_meta, brief_body = parse_md_with_frontmatter(brief_path)

    profile = brief_meta.get("profile", "unknown")
    slug = brief_meta.get("slug", post_dir.name)
    format_ = brief_meta.get("format", "feed_4x5")
    engine = brief_meta.get("engine") or DEFAULT_ENGINE
    size = FORMAT_TO_SIZE.get(format_, "1024x1280")
    output_filename = FORMAT_TO_FILENAME.get(format_, "feed.png")

    # A carousel with a structured `slides:` list materializes the carousel template,
    # which loops slides and routes each by modality (html vs image). Otherwise the
    # single-image template. This keeps "carousel = N slides" out of agent judgement.
    slides = brief_meta.get("slides")
    is_carousel = format_.startswith("carousel") and isinstance(slides, list) and len(slides) > 0

    if is_carousel:
        template_path = template_dir / "carousel.py.tmpl"
        if not template_path.is_file():
            raise FileNotFoundError(f"carousel.py.tmpl not found in {template_dir}")
        materialized = (
            template_path.read_text()
            .replace("{{profile}}", profile)
            .replace("{{slug}}", slug)
            .replace("{{engine}}", engine)
            .replace("{{format}}", format_)
            .replace("{{size}}", size)
            .replace("{{slides_repr}}", repr(slides))
        )
    else:
        template_path = template_dir / "craft.py.tmpl"
        if not template_path.is_file():
            raise FileNotFoundError(f"craft.py.tmpl not found in {template_dir}")
        task = brief_body.strip()  # Task = brief body (everything after frontmatter)
        materialized = (
            template_path.read_text()
            .replace("{{profile}}", profile)
            .replace("{{slug}}", slug)
            .replace("{{output_filename}}", output_filename)
            .replace("{{engine}}", engine)
            .replace("{{format}}", format_)
            .replace("{{size}}", size)
            .replace("{{task_repr}}", repr(task))
        )

    out = post_dir / "craft.py"
    out.write_text(materialized)
    out.chmod(0o755)
    return out
