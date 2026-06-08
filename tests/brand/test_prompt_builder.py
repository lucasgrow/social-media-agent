"""Tests for prompt_builder.build_prompt."""
from pathlib import Path

from social_media_agent.brand.brand_loader import list_brand_pages, parse_design_md, parse_voice_md
from social_media_agent.brand.prompt_builder import build_prompt

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_build_prompt_returns_text_and_refs():
    """build_prompt returns (text_prompt: str, image_refs: list[Path])."""
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    pages = list_brand_pages(FIXTURES / "sample_brand_pages")

    result = build_prompt(
        task="Generate a feed post",
        design=design_meta,
        voice=voice_meta,
        brand_pages=pages,
        extra_refs=[],
    )
    assert isinstance(result, tuple)
    text, refs = result
    assert isinstance(text, str)
    assert isinstance(refs, list)
    assert all(isinstance(r, Path) for r in refs)


def test_build_prompt_text_includes_task_description():
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    pages = list_brand_pages(FIXTURES / "sample_brand_pages")

    text, _ = build_prompt(
        task="UNIQUE_TASK_MARKER_XYZ",
        design=design_meta,
        voice=voice_meta,
        brand_pages=pages,
        extra_refs=[],
    )
    assert "UNIQUE_TASK_MARKER_XYZ" in text


def test_build_prompt_text_includes_palette_hex():
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    pages = list_brand_pages(FIXTURES / "sample_brand_pages")

    text, _ = build_prompt(
        task="Test",
        design=design_meta,
        voice=voice_meta,
        brand_pages=pages,
        extra_refs=[],
    )
    assert "#7A4658" in text  # primary
    assert "#F1E2C2" in text  # background
    assert "#D4A574" in text  # accent


def test_build_prompt_text_includes_fonts():
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    pages = list_brand_pages(FIXTURES / "sample_brand_pages")

    text, _ = build_prompt(
        task="Test",
        design=design_meta,
        voice=voice_meta,
        brand_pages=pages,
        extra_refs=[],
    )
    assert "Oswald Bold" in text
    assert "Cormorant Garamond" in text


def test_build_prompt_image_refs_include_all_brand_pages():
    """All brand_pages passed are present in the image_refs list."""
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    pages = list_brand_pages(FIXTURES / "sample_brand_pages")

    _, refs = build_prompt(
        task="Test",
        design=design_meta,
        voice=voice_meta,
        brand_pages=pages,
        extra_refs=[],
    )
    for page in pages:
        assert page in refs


def test_build_prompt_image_refs_extra_refs_come_first():
    """extra_refs come BEFORE brand_pages in image[] order."""
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    pages = list_brand_pages(FIXTURES / "sample_brand_pages")
    extra = [FIXTURES / "sample_brand_pages" / "01-cover.png"]

    _, refs = build_prompt(
        task="Test",
        design=design_meta,
        voice=voice_meta,
        brand_pages=pages,
        extra_refs=extra,
    )
    assert refs[0] == extra[0]


def test_build_prompt_mark_type_none_adds_explicit_no_emblem_rule():
    """When DESIGN.md says mark.type=none, prompt explicitly forbids emblem."""
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    pages = list_brand_pages(FIXTURES / "sample_brand_pages")

    assert design_meta["mark"]["type"] == "none"

    text, _ = build_prompt(
        task="Test",
        design=design_meta,
        voice=voice_meta,
        brand_pages=pages,
        extra_refs=[],
    )
    text_lower = text.lower()
    assert "no emblem" in text_lower or "no monogram" in text_lower
    assert "mark" in text_lower


def test_build_prompt_mark_type_image_does_not_add_no_emblem_rule():
    """When mark.type=image, the no-emblem rule is NOT added."""
    design_meta = {
        "palette": {"primary": "#000000"},
        "fonts": {"display": "Arial"},
        "mark": {"type": "image", "path": "assets/logo.png"},
    }
    text, _ = build_prompt(
        task="Test",
        design=design_meta,
        voice={},
        brand_pages=[],
        extra_refs=[],
    )
    assert "no emblem" not in text.lower()


def test_build_prompt_with_learnings_path_injects_section():
    """When learnings_path provided + file exists, prompt contains 'RECENT LEARNINGS' section."""
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    pages = list_brand_pages(FIXTURES / "sample_brand_pages")

    text, _ = build_prompt(
        task="Test",
        design=design_meta,
        voice=voice_meta,
        brand_pages=pages,
        extra_refs=[],
        learnings_path=FIXTURES / "sample_learnings.md",
    )
    assert "RECENT LEARNINGS" in text
    assert "Cormorant Italic dominante" in text or "Oswald Bold em info posts" in text


def test_build_prompt_without_learnings_path_omits_section():
    """No learnings_path → no RECENT LEARNINGS section."""
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")
    pages = list_brand_pages(FIXTURES / "sample_brand_pages")

    text, _ = build_prompt(
        task="Test",
        design=design_meta,
        voice=voice_meta,
        brand_pages=pages,
        extra_refs=[],
    )
    assert "RECENT LEARNINGS" not in text


def test_build_prompt_with_missing_learnings_file_omits_section():
    """learnings_path given but file missing → no error, no section."""
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")

    text, _ = build_prompt(
        task="Test",
        design=design_meta,
        voice=voice_meta,
        brand_pages=[],
        extra_refs=[],
        learnings_path=FIXTURES / "nonexistent_learnings.md",
    )
    assert "RECENT LEARNINGS" not in text


def test_build_prompt_learnings_limit_caps_items():
    """learnings_limit=2 caps to top-2 do_this + top-2 avoid."""
    design_meta, _ = parse_design_md(FIXTURES / "sample_design.md")
    voice_meta, _ = parse_voice_md(FIXTURES / "sample_voice.md")

    text, _ = build_prompt(
        task="Test",
        design=design_meta,
        voice=voice_meta,
        brand_pages=[],
        extra_refs=[],
        learnings_path=FIXTURES / "sample_learnings.md",
        learnings_limit=1,
    )
    # Only top-1 of each → 2 items max in learnings section
    section_start = text.index("RECENT LEARNINGS")
    section = text[section_start:]
    # Count bullets in the learnings section only (truncate at next blank line+section header)
    learnings_bullets = [line for line in section.split("\n") if line.startswith("- ")]
    assert len(learnings_bullets) <= 2  # top-1 do_this + top-1 avoid
