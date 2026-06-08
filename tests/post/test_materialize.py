"""Tests for post.materialize.materialize_craft_py."""
from pathlib import Path

import pytest

from social_media_agent.post.materialize import materialize_craft_py

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE_DIR = REPO_ROOT / "src" / "social_media_agent" / "templates"


def _make_brief(post_dir: Path, profile: str, slug: str, format_: str = "feed_4x5",
                engine: str = "openai_gpt_image_2", task: str = "Test task"):
    brief = f"""---
profile: {profile}
slug: {slug}
format: {format_}
engine: {engine}
context: utility
created: 2026-05-27
---

# Brief — {slug}

{task}
"""
    (post_dir / "brief.md").write_text(brief)


def test_materialize_creates_craft_py(tmp_path):
    post_dir = tmp_path / "01-my-post"
    post_dir.mkdir()
    _make_brief(post_dir, profile="test-prof", slug="01-my-post")

    result = materialize_craft_py(post_dir, template_dir=TEMPLATE_DIR)
    assert result == post_dir / "craft.py"
    assert result.is_file()


def test_materialize_substitutes_profile_slug_format(tmp_path):
    post_dir = tmp_path / "01-my-post"
    post_dir.mkdir()
    _make_brief(post_dir, profile="test-prof", slug="01-my-post",
                format_="carousel_4x5", task="Specific task content")

    craft = materialize_craft_py(post_dir, template_dir=TEMPLATE_DIR)
    text = craft.read_text()
    assert 'profiles" / "test-prof"' in text
    assert "Specific task content" in text


def test_materialize_bakes_engine_and_format(tmp_path):
    """Single craft template bakes ENGINE + FORMAT; size is resolved at runtime."""
    post_dir = tmp_path / "post-x"
    post_dir.mkdir()
    _make_brief(post_dir, profile="p", slug="post-x", format_="story_9x16_still",
                engine="gemini_image")
    text = materialize_craft_py(post_dir, template_dir=TEMPLATE_DIR).read_text()
    assert 'ENGINE = "gemini_image"' in text
    assert 'FORMAT = "story_9x16_still"' in text


def test_materialize_size_resolves_per_format_and_engine():
    """resolve_gen_kwargs maps format → openai size / gemini aspect ratio."""
    from social_media_agent.engines.spec import resolve_gen_kwargs

    assert resolve_gen_kwargs("openai_gpt_image_2", "feed_4x5")["size"] == "1024x1280"
    assert resolve_gen_kwargs("openai_gpt_image_2", "feed_1x1")["size"] == "1024x1024"
    assert resolve_gen_kwargs("openai_gpt_image_2", "story_9x16_still")["size"] == "1024x1536"
    assert resolve_gen_kwargs("gemini_image", "story_9x16_still")["aspect_ratio"] == "9:16"


def test_materialize_output_filename_matches_format(tmp_path):
    """format=feed_* → output 'feed.png'; story_* → 'story.png'"""
    for fmt, expected_filename in [
        ("feed_4x5", "feed.png"),
        ("story_9x16_still", "story.png"),
        ("carousel_4x5", "carousel.png"),
    ]:
        post_dir = tmp_path / f"post-{fmt}"
        post_dir.mkdir()
        _make_brief(post_dir, profile="p", slug=f"post-{fmt}", format_=fmt)
        craft = materialize_craft_py(post_dir, template_dir=TEMPLATE_DIR)
        text = craft.read_text()
        assert f'"{expected_filename}"' in text


def test_materialize_raises_if_brief_md_missing(tmp_path):
    post_dir = tmp_path / "empty"
    post_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="brief.md"):
        materialize_craft_py(post_dir, template_dir=TEMPLATE_DIR)


def test_materialize_raises_if_template_missing(tmp_path):
    post_dir = tmp_path / "p"
    post_dir.mkdir()
    _make_brief(post_dir, profile="x", slug="p")
    with pytest.raises(FileNotFoundError, match="craft.py.tmpl"):
        materialize_craft_py(post_dir, template_dir=tmp_path / "no-templates")


def test_materialize_handles_triple_quote_in_task_body(tmp_path):
    """Brief body with triple quotes (markdown code blocks) must not break craft.py syntax."""
    post_dir = tmp_path / "01-codeblock-post"
    post_dir.mkdir()
    fence = "`" * 3
    brief = (
        "---\n"
        "profile: test-prof\n"
        "slug: 01-codeblock-post\n"
        "format: feed_4x5\n"
        "engine: openai_gpt_image_2\n"
        "context: utility\n"
        "created: 2026-05-28\n"
        "---\n"
        "\n"
        "# Brief with code block\n"
        "\n"
        "Some text then a code block:\n"
        "\n"
        f"{fence}python\n"
        'task = """do something"""\n'
        f"{fence}\n"
        "\n"
        "More text.\n"
    )
    (post_dir / "brief.md").write_text(brief)

    craft = materialize_craft_py(post_dir, template_dir=TEMPLATE_DIR)
    # Must produce valid Python — compile() raises SyntaxError if broken
    compile(craft.read_text(), str(craft), "exec")
