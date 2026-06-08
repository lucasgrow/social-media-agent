"""Tests for brand_loader.parse_design_md."""
from pathlib import Path

import pytest

from social_media_agent.brand.brand_loader import parse_design_md

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_parse_design_md_returns_meta_and_body():
    """parse_design_md returns (meta_dict, body_str) tuple."""
    result = parse_design_md(FIXTURES / "sample_design.md")
    assert isinstance(result, tuple)
    assert len(result) == 2
    meta, body = result
    assert isinstance(meta, dict)
    assert isinstance(body, str)


def test_parse_design_md_extracts_yaml_frontmatter():
    """YAML frontmatter parsed into dict with expected keys."""
    meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    assert meta["name"] == "example-brand"
    assert meta["ig_handle"] == "@examplebrand"
    assert meta["default_engine"] == "openai_gpt_image_2"
    assert meta["formats_enabled"] == ["feed_4x5", "carousel_4x5"]


def test_parse_design_md_extracts_nested_palette():
    """Nested dicts (palette, fonts, mark) preserved."""
    meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    assert meta["palette"]["primary"] == "#7A4658"
    assert meta["fonts"]["display"] == "Oswald Bold"
    assert meta["mark"]["type"] == "none"


def test_parse_design_md_body_is_markdown_after_frontmatter():
    """Body string is everything after the closing ---."""
    _, body = parse_design_md(FIXTURES / "sample_design.md")
    assert body.lstrip().startswith("# Brand: Example Brand")
    assert "## Section heading" in body


def test_parse_design_md_missing_file_raises():
    """Nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        parse_design_md(FIXTURES / "nonexistent.md")


def test_parse_design_md_no_frontmatter_returns_empty_meta():
    """File without --- frontmatter returns empty dict + full content as body."""
    tmp = FIXTURES / "_no_frontmatter.md"
    tmp.write_text("# Just markdown\n\nNo frontmatter here.\n")
    try:
        meta, body = parse_design_md(tmp)
        assert meta == {}
        assert "# Just markdown" in body
    finally:
        tmp.unlink()


from social_media_agent.brand.brand_loader import list_brand_pages  # noqa: E402


def test_list_brand_pages_returns_sorted_png_paths():
    """list_brand_pages returns absolute paths to PNGs, sorted by filename."""
    pages_dir = FIXTURES / "sample_brand_pages"
    result = list_brand_pages(pages_dir)
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(p, Path) for p in result)
    names = [p.name for p in result]
    assert names == ["01-cover.png", "02-filosofia.png", "03-paleta.png"]


def test_list_brand_pages_empty_dir_returns_empty_list():
    """Empty directory returns empty list (not error)."""
    empty = FIXTURES / "_empty_pages"
    empty.mkdir(exist_ok=True)
    try:
        assert list_brand_pages(empty) == []
    finally:
        empty.rmdir()


def test_list_brand_pages_missing_dir_raises():
    """Nonexistent directory raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        list_brand_pages(FIXTURES / "nonexistent_dir")


from social_media_agent.brand.brand_loader import parse_voice_md  # noqa: E402


def test_parse_voice_md_returns_meta_and_body():
    """parse_voice_md returns (meta_dict, body_str)."""
    meta, body = parse_voice_md(FIXTURES / "sample_voice.md")
    assert meta["language"] == "en"
    assert isinstance(body, str)
    assert "# Voice — Example Brand" in body


def test_parse_voice_md_extracts_lists():
    """tone, go_words, no_go_words preserved as lists."""
    meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    assert meta["tone"] == ["calm", "no emojis in the artwork"]
    assert meta["go_words"] == ["clear", "considered", "simple"]
    assert "synergy" in meta["no_go_words"]


def test_parse_voice_md_extracts_contexts():
    """contexts dict with per-context pattern preserved."""
    meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    assert "announcement" in meta["contexts"]
    assert meta["contexts"]["announcement"]["pattern"].startswith("short hooks")


def test_parse_voice_md_missing_file_raises():
    """Nonexistent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        parse_voice_md(FIXTURES / "nonexistent_voice.md")
