"""Tests for post.bootstrap.bootstrap_post."""
from social_media_agent.post.bootstrap import bootstrap_post


def _make_profile(tmp_path):
    p = tmp_path / "profiles" / "test-profile"
    (p / "brand-kit" / "pages").mkdir(parents=True)
    (p / "brand-kit" / "DESIGN.md").write_text(
        "---\nname: test-profile\nformats_enabled:\n  - feed_4x5\n"
        "default_engine: openai_gpt_image_2\n---\n"
    )
    (p / "VOICE.md").write_text("---\nlanguage: pt-BR\n---\n")
    return p


def test_bootstrap_creates_post_dir_with_expected_structure(tmp_path):
    profile = _make_profile(tmp_path)
    source_files = [tmp_path / "fake-source.jpg"]
    source_files[0].write_bytes(b"fake-image")

    result = bootstrap_post(
        profile_dir=profile,
        slug="my-test-post",
        year_month="2026-05",
        format_="feed_4x5",
        engine="openai_gpt_image_2",
        source_url="https://x.com/y/status/1",
        source_files=source_files,
        source_meta={"title": "My Test"},
    )

    post_dir = result["post_dir"]
    assert post_dir.exists()
    assert post_dir.parent.name == "2026-05"
    assert post_dir.name == "01-my-test-post"   # auto-numbered as first in month
    assert (post_dir / "source" / "fake-source.jpg").exists()
    assert (post_dir / "source" / "original-link.txt").read_text().strip() == "https://x.com/y/status/1"
    assert (post_dir / "source" / "meta.json").exists()
    assert (post_dir / "brief.md").exists()
    assert "feed_4x5" in (post_dir / "brief.md").read_text()


def test_bootstrap_auto_numbers_subsequent_posts_in_same_month(tmp_path):
    profile = _make_profile(tmp_path)
    src = tmp_path / "s.jpg"
    src.write_bytes(b"x")

    # First post
    r1 = bootstrap_post(profile_dir=profile, slug="first", year_month="2026-05",
                        format_="feed_4x5", engine="openai_gpt_image_2",
                        source_url=None, source_files=[src], source_meta={})
    assert r1["post_dir"].name == "01-first"

    # Second post in same month
    r2 = bootstrap_post(profile_dir=profile, slug="second", year_month="2026-05",
                        format_="feed_4x5", engine="openai_gpt_image_2",
                        source_url=None, source_files=[src], source_meta={})
    assert r2["post_dir"].name == "02-second"


def test_bootstrap_handles_empty_source_files(tmp_path):
    """Posts without external source (e.g., pure text brief) still get a source/ dir."""
    profile = _make_profile(tmp_path)
    result = bootstrap_post(profile_dir=profile, slug="text-only", year_month="2026-05",
                            format_="feed_4x5", engine="openai_gpt_image_2",
                            source_url=None, source_files=[], source_meta={})
    assert (result["post_dir"] / "source").is_dir()
    # source has at least the meta.json (even if empty)
    assert (result["post_dir"] / "source" / "meta.json").exists()


def test_bootstrap_brief_md_includes_engine_and_format(tmp_path):
    profile = _make_profile(tmp_path)
    src = tmp_path / "s.jpg"
    src.write_bytes(b"x")
    result = bootstrap_post(profile_dir=profile, slug="check-brief", year_month="2026-05",
                            format_="carousel_4x5", engine="gemini_3_pro_image",
                            source_url=None, source_files=[src], source_meta={})
    brief = (result["post_dir"] / "brief.md").read_text()
    assert "carousel_4x5" in brief
    assert "gemini_3_pro_image" in brief
    assert "test-profile" in brief
