"""Carousel materialization routes to the looping, modality-aware template."""
from pathlib import Path

from social_media_agent.post.materialize import materialize_craft_py

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = REPO_ROOT / "src" / "social_media_agent" / "templates"

CAROUSEL_BRIEF = """\
---
profile: example-brand
slug: facts
format: carousel_4x5
slides:
  - name: cover
    render: image
    ref: source/01.jpg
    task: a bold cover photograph
  - name: fact
    render: html
    title: THE FACT
    paragraphs:
      - A short paragraph of body copy for the text slide.
    source: SOURCE LINE
---

# Brief body
"""

SINGLE_BRIEF = """\
---
profile: example-brand
slug: one
format: feed_4x5
---

A single feed image of a candle.
"""


def test_carousel_brief_materializes_looping_template(tmp_path):
    post_dir = tmp_path / "01-facts"
    post_dir.mkdir()
    (post_dir / "brief.md").write_text(CAROUSEL_BRIEF)

    craft = materialize_craft_py(post_dir, template_dir=TEMPLATE_DIR)
    text = craft.read_text()

    # Loops slides + routes by modality + both renderers wired in.
    assert "for i, slide in enumerate(SLIDES" in text
    assert "classify(slide)" in text
    assert "render_html" in text  # html path
    assert "edit(" in text and "generate(" in text  # image path
    # The slides list was injected (not left as a placeholder).
    assert "{{slides_repr}}" not in text
    assert "SOURCE LINE" in text
    assert "a bold cover photograph" in text


def test_single_brief_still_uses_single_template(tmp_path):
    post_dir = tmp_path / "01-one"
    post_dir.mkdir()
    (post_dir / "brief.md").write_text(SINGLE_BRIEF)

    craft = materialize_craft_py(post_dir, template_dir=TEMPLATE_DIR)
    text = craft.read_text()

    assert "for i, slide in enumerate(SLIDES" not in text  # not the carousel loop
    assert "candle" in text  # task injected from brief body


def test_carousel_without_slides_falls_back_to_single(tmp_path):
    # format=carousel but no slides[] → single template (no crash).
    post_dir = tmp_path / "01-nocarousel"
    post_dir.mkdir()
    (post_dir / "brief.md").write_text(
        "---\nprofile: p\nslug: s\nformat: carousel_4x5\n---\n\nbody text\n"
    )
    craft = materialize_craft_py(post_dir, template_dir=TEMPLATE_DIR)
    assert "for i, slide in enumerate(SLIDES" not in craft.read_text()
