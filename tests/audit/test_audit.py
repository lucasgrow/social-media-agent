"""Tests for audit.audit.run_audit (orchestrator)."""
from unittest.mock import patch

from PIL import Image

from social_media_agent.audit.audit import run_audit


def _setup_profile_with_post(tmp_path):
    profile = tmp_path / "test-profile"
    (profile / "brand-kit" / "pages").mkdir(parents=True)
    (profile / "brand-kit" / "DESIGN.md").write_text("---\nname: test-profile\n---\n")
    (profile / "VOICE.md").write_text("---\nlanguage: pt-BR\n---\n")
    # Brand pages (mocks)
    for name in ("03-paleta.png", "04-tipografia.png", "08-donts.png"):
        Image.new("RGB", (10, 10), "white").save(profile / "brand-kit" / "pages" / name)
    # Post with final output + decisions
    post = profile / "posts" / "2026-05" / "01-test"
    final = post / "outputs" / "final"
    final.mkdir(parents=True)
    Image.new("RGB", (10, 10), "blue").save(final / "feed.png")
    (post / "decisions.md").write_text(
        "# Decisions log — 01-test\n\n"
        "## v1\n- timestamp: 2026-05-25 10:00:00\n- note: ok\n\n"
        "<details><summary>prompt</summary>\n\n```\nmy prompt v1\n```\n</details>\n"
    )
    return profile


def test_run_audit_returns_summary_dict(tmp_path):
    profile = _setup_profile_with_post(tmp_path)

    fake_drift = '{"palette_drift": false, "font_drift": false, "donts_violations": []}'
    fake_patterns = '{"do_this": ["pat1"], "avoid": [], "voice_patterns": [], "engagement_signals": []}'

    with patch("social_media_agent.audit.drift_detector.analyze_image", return_value=fake_drift), \
         patch("social_media_agent.audit.pattern_extractor.extract_structured", return_value=fake_patterns):
        result = run_audit(profile_dir=profile, api_key="sk-test")

    assert result["posts_analyzed"] == 1
    assert "learnings_path" in result
    assert result["learnings_path"] == profile / "learnings.md"
    assert (profile / "learnings.md").is_file()


def test_run_audit_writes_learnings_with_extracted_patterns(tmp_path):
    profile = _setup_profile_with_post(tmp_path)

    fake_drift = '{"palette_drift": false, "font_drift": false, "donts_violations": []}'
    fake_patterns = '{"do_this": ["UNIQUE_PATTERN_MARKER"], "avoid": [], "voice_patterns": [], "engagement_signals": []}'

    with patch("social_media_agent.audit.drift_detector.analyze_image", return_value=fake_drift), \
         patch("social_media_agent.audit.pattern_extractor.extract_structured", return_value=fake_patterns):
        run_audit(profile_dir=profile, api_key="sk-test")

    text = (profile / "learnings.md").read_text()
    assert "UNIQUE_PATTERN_MARKER" in text


def test_run_audit_with_no_posts_writes_empty_learnings(tmp_path):
    profile = tmp_path / "empty-profile"
    (profile / "brand-kit" / "pages").mkdir(parents=True)
    (profile / "brand-kit" / "DESIGN.md").write_text("---\n---\n")
    (profile / "VOICE.md").write_text("---\n---\n")

    fake_patterns = '{"do_this": [], "avoid": [], "voice_patterns": [], "engagement_signals": []}'
    with patch("social_media_agent.audit.pattern_extractor.extract_structured", return_value=fake_patterns):
        result = run_audit(profile_dir=profile, api_key="sk-test")

    assert result["posts_analyzed"] == 0
    assert (profile / "learnings.md").is_file()
    text = (profile / "learnings.md").read_text()
    assert "(none)" in text or "no drift detected" in text
