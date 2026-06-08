"""Tests for audit.learnings_writer."""
from social_media_agent.audit.learnings_writer import write_learnings


def _patterns():
    return {
        "do_this": ["use Cormorant in info posts"],
        "avoid": ["solid plum-wine blocks"],
        "voice_patterns": ["short hooks"],
        "engagement_signals": ["post 01 had high engagement"],
    }


def _drifts():
    return [
        {"post_slug": "01-test", "palette_drift": False, "font_drift": True, "donts_violations": ["used emoji on slide"]},
    ]


def test_write_learnings_creates_file(tmp_path):
    out = write_learnings(profile_dir=tmp_path, patterns=_patterns(), drifts=_drifts(), posts_analyzed=5)
    assert out == tmp_path / "learnings.md"
    assert out.is_file()


def test_write_learnings_has_frontmatter_with_last_audit(tmp_path):
    write_learnings(profile_dir=tmp_path, patterns=_patterns(), drifts=_drifts(), posts_analyzed=5)
    text = (tmp_path / "learnings.md").read_text()
    assert text.startswith("---\n")
    assert "last_audit:" in text
    assert "posts_analyzed: 5" in text


def test_write_learnings_includes_all_sections(tmp_path):
    write_learnings(profile_dir=tmp_path, patterns=_patterns(), drifts=_drifts(), posts_analyzed=5)
    text = (tmp_path / "learnings.md").read_text()
    assert "Do this" in text
    assert "Avoid" in text
    assert "Voice patterns" in text
    assert "Engagement signals" in text
    assert "Brand drift" in text


def test_write_learnings_includes_pattern_items(tmp_path):
    write_learnings(profile_dir=tmp_path, patterns=_patterns(), drifts=_drifts(), posts_analyzed=5)
    text = (tmp_path / "learnings.md").read_text()
    assert "use Cormorant in info posts" in text
    assert "solid plum-wine blocks" in text
    assert "short hooks" in text


def test_write_learnings_includes_drift_items(tmp_path):
    write_learnings(profile_dir=tmp_path, patterns=_patterns(), drifts=_drifts(), posts_analyzed=5)
    text = (tmp_path / "learnings.md").read_text()
    assert "01-test" in text
    assert "font_drift" in text
    assert "used emoji on slide" in text


def test_write_learnings_overwrites_existing(tmp_path):
    (tmp_path / "learnings.md").write_text("OLD CONTENT")
    write_learnings(profile_dir=tmp_path, patterns=_patterns(), drifts=_drifts(), posts_analyzed=5)
    text = (tmp_path / "learnings.md").read_text()
    assert "OLD CONTENT" not in text
    assert "Do this" in text
