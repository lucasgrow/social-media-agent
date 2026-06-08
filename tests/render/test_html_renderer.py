"""Tests for the HTML slide renderer (no real browser launched)."""
from unittest.mock import patch

import pytest

from social_media_agent.render.html_renderer import render_html, text_slide_html

DESIGN = {
    "palette": {"background": "#0A0A0A", "text_light": "#F4F4F4", "accent": "#C8102E"},
    "fonts": {"display": "Helvetica Neue Bold", "serif": "EB Garamond"},
}


def test_text_slide_html_contains_content_and_fonts():
    html = text_slide_html(
        DESIGN,
        title="The Legend of St. Francis",
        paragraphs=["In the town of Gubbio a fierce wolf preyed on the people.", "Francis went out."],
        source="RETOLD FROM THE FIORETTI",
    )
    assert "The Legend of St. Francis" in html
    assert "town of Gubbio" in html
    assert "RETOLD FROM THE FIORETTI" in html
    assert "EB Garamond" in html  # serif body font
    assert "Helvetica Neue Bold" in html  # display font
    assert "#0A0A0A" in html  # brand background


def test_text_slide_html_escapes_html():
    html = text_slide_html(DESIGN, title="A & B <x>", paragraphs=["1 < 2 & 3 > 0"])
    assert "&amp;" in html and "&lt;" in html
    assert "<x>" not in html  # raw tag must be escaped, not injected


def test_render_html_raises_clear_error_when_chromium_missing(tmp_path):
    boom = Exception("Executable doesn't exist at /path; run playwright install")
    with patch("social_media_agent.render.html_renderer.sync_playwright", side_effect=boom):
        with pytest.raises(RuntimeError, match="playwright install chromium"):
            render_html("<html></html>", tmp_path / "out.png")
