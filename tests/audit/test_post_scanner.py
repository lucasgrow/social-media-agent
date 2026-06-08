"""Tests for audit.post_scanner."""
from social_media_agent.audit.post_scanner import scan_posts


def _make_post(profile_dir, year_month, slug, with_final=True, with_decisions=True):
    post = profile_dir / "posts" / year_month / slug
    post.mkdir(parents=True)
    (post / "brief.md").write_text(f"---\nslug: {slug}\n---\n")
    if with_final:
        final = post / "outputs" / "final"
        final.mkdir(parents=True)
        (final / "feed.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    if with_decisions:
        (post / "decisions.md").write_text(f"# Decisions — {slug}\n")
    return post


def test_scan_posts_returns_list_of_dicts(tmp_path):
    profile = tmp_path / "test-profile"
    _make_post(profile, "2026-05", "01-first")
    result = scan_posts(profile)
    assert isinstance(result, list)
    assert all(isinstance(item, dict) for item in result)


def test_scan_posts_includes_post_dir_final_outputs_decisions(tmp_path):
    profile = tmp_path / "test-profile"
    post = _make_post(profile, "2026-05", "01-first")
    result = scan_posts(profile)
    assert len(result) == 1
    entry = result[0]
    assert entry["post_dir"] == post
    assert post / "outputs" / "final" / "feed.png" in entry["final_outputs"]
    assert entry["decisions_path"] == post / "decisions.md"


def test_scan_posts_skips_posts_without_final(tmp_path):
    profile = tmp_path / "test-profile"
    _make_post(profile, "2026-05", "01-finalized", with_final=True)
    _make_post(profile, "2026-05", "02-draft-only", with_final=False)
    result = scan_posts(profile)
    slugs = [r["post_dir"].name for r in result]
    assert "01-finalized" in slugs
    assert "02-draft-only" not in slugs


def test_scan_posts_handles_missing_decisions_md(tmp_path):
    profile = tmp_path / "test-profile"
    _make_post(profile, "2026-05", "01-no-decisions", with_decisions=False)
    result = scan_posts(profile)
    assert len(result) == 1
    assert result[0]["decisions_path"] is None


def test_scan_posts_sorts_by_post_dir_path(tmp_path):
    profile = tmp_path / "test-profile"
    _make_post(profile, "2026-06", "01-june")
    _make_post(profile, "2026-05", "02-may-second")
    _make_post(profile, "2026-05", "01-may-first")
    result = scan_posts(profile)
    names = [r["post_dir"].name for r in result]
    assert names == ["01-may-first", "02-may-second", "01-june"]


def test_scan_posts_returns_empty_if_no_posts_dir(tmp_path):
    profile = tmp_path / "empty-profile"
    profile.mkdir()
    assert scan_posts(profile) == []
