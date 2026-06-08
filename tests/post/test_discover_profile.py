"""Tests for post.discover_profile."""
import pytest

from social_media_agent.post.discover_profile import (
    ProfileAmbiguous,
    ProfileNotFound,
    discover_profile,
    list_profiles,
)


def _make_profile(profiles_dir, name):
    """Create a minimal valid profile structure."""
    p = profiles_dir / name
    (p / "brand-kit" / "pages").mkdir(parents=True)
    (p / "brand-kit" / "DESIGN.md").write_text("---\nname: " + name + "\n---\n")
    (p / "VOICE.md").write_text("---\nlanguage: pt-BR\n---\n")
    return p


def test_list_profiles_returns_sorted_names(tmp_path):
    _make_profile(tmp_path, "zebra")
    _make_profile(tmp_path, "alpha")
    _make_profile(tmp_path, "mike")
    assert list_profiles(tmp_path) == ["alpha", "mike", "zebra"]


def test_list_profiles_empty_returns_empty_list(tmp_path):
    assert list_profiles(tmp_path) == []


def test_list_profiles_ignores_non_directories(tmp_path):
    _make_profile(tmp_path, "real")
    (tmp_path / "README.md").write_text("not a profile")
    (tmp_path / ".gitkeep").touch()
    assert list_profiles(tmp_path) == ["real"]


def test_list_profiles_ignores_profiles_missing_design_md(tmp_path):
    _make_profile(tmp_path, "valid")
    (tmp_path / "halfbaked" / "brand-kit").mkdir(parents=True)
    # no DESIGN.md
    assert list_profiles(tmp_path) == ["valid"]


def test_discover_profile_returns_path_when_name_given(tmp_path):
    p = _make_profile(tmp_path, "example-brand")
    result = discover_profile(profiles_dir=tmp_path, name="example-brand")
    assert result == p


def test_discover_profile_raises_when_name_not_found(tmp_path):
    _make_profile(tmp_path, "existing")
    with pytest.raises(ProfileNotFound, match="nonexistent"):
        discover_profile(profiles_dir=tmp_path, name="nonexistent")


def test_discover_profile_auto_picks_single_profile_when_no_name(tmp_path):
    p = _make_profile(tmp_path, "only-one")
    result = discover_profile(profiles_dir=tmp_path, name=None)
    assert result == p


def test_discover_profile_raises_ambiguous_when_multiple_profiles_no_name(tmp_path):
    _make_profile(tmp_path, "a")
    _make_profile(tmp_path, "b")
    with pytest.raises(ProfileAmbiguous) as exc:
        discover_profile(profiles_dir=tmp_path, name=None)
    assert "a" in exc.value.candidates
    assert "b" in exc.value.candidates


def test_discover_profile_raises_not_found_when_zero_profiles_no_name(tmp_path):
    with pytest.raises(ProfileNotFound, match="No profiles"):
        discover_profile(profiles_dir=tmp_path, name=None)
