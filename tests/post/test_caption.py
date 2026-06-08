"""Tests for post.caption.create_caption_skeleton."""
import pytest

from social_media_agent.post.caption import create_caption_skeleton


def _make_post(tmp_path):
    profile = tmp_path / "profiles" / "test"
    (profile / "brand-kit").mkdir(parents=True)
    (profile / "brand-kit" / "DESIGN.md").write_text(
        "---\nname: test\nig_handle: '@test'\n---\n"
    )
    (profile / "VOICE.md").write_text(
        "---\nlanguage: pt-BR\ntone: [intimista]\n"
        "contexts:\n  devocional:\n    pattern: 'short hooks + bible echo'\n---\n"
    )
    post = profile / "posts" / "2026-05" / "01-test"
    post.mkdir(parents=True)
    (post / "brief.md").write_text(
        "---\nprofile: test\nslug: 01-test\ncontext: devocional\n---\n# Brief\n"
    )
    return post, profile


def test_create_caption_skeleton_writes_caption_md(tmp_path):
    post, profile = _make_post(tmp_path)
    result = create_caption_skeleton(post_dir=post, profile_dir=profile)
    assert result == post / "caption.md"
    assert result.is_file()


def test_create_caption_skeleton_includes_ig_handle_and_context(tmp_path):
    post, profile = _make_post(tmp_path)
    create_caption_skeleton(post_dir=post, profile_dir=profile)
    text = (post / "caption.md").read_text()
    assert "@test" in text
    assert "devocional" in text


def test_create_caption_skeleton_includes_voice_pattern_hint(tmp_path):
    post, profile = _make_post(tmp_path)
    create_caption_skeleton(post_dir=post, profile_dir=profile)
    text = (post / "caption.md").read_text()
    assert "short hooks + bible echo" in text


def test_create_caption_skeleton_does_not_overwrite_existing(tmp_path):
    post, profile = _make_post(tmp_path)
    (post / "caption.md").write_text("existing caption — do not overwrite")
    create_caption_skeleton(post_dir=post, profile_dir=profile)
    assert (post / "caption.md").read_text() == "existing caption — do not overwrite"


def test_create_caption_skeleton_raises_if_brief_missing(tmp_path):
    post = tmp_path / "empty"
    post.mkdir()
    profile = tmp_path / "profiles" / "test"
    (profile / "brand-kit").mkdir(parents=True)
    (profile / "brand-kit" / "DESIGN.md").write_text("---\n---\n")
    (profile / "VOICE.md").write_text("---\n---\n")
    with pytest.raises(FileNotFoundError):
        create_caption_skeleton(post_dir=post, profile_dir=profile)
