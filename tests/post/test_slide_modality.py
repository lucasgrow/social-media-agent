"""Tests for the deterministic per-slide modality rule.

Rule: HTML only when the slide follows a clear template standard (templated `kind`) or is
explicitly `render: html`. Everything else — art-directed/expressive/unknown — is `image`.
"""
from social_media_agent.post.slide_modality import HTML, IMAGE, classify, is_text_dominant


def test_explicit_render_wins():
    assert classify({"render": "html", "task": "a photo", "ref": "x.jpg"}) == HTML
    assert classify({"render": "image", "kind": "legend"}) == IMAGE


def test_templated_kinds_route_to_html():
    for kind in ("legend", "quote", "info", "hours", "table", "prose"):
        assert classify({"kind": kind}) == HTML, kind
    assert is_text_dominant({"kind": "legend"}) is True


def test_art_directed_or_unknown_routes_to_image():
    # A typographic cover is text-heavy but art-directed → NOT html.
    assert classify({"kind": "cover", "title": "MAGNIFICA HUMANITAS"}) == IMAGE
    assert classify({"kind": "headline"}) == IMAGE
    # Body text without a recognised template standard is not auto-html either.
    assert classify({"paragraphs": ["lots of art-directed text"]}) == IMAGE


def test_default_is_image_when_no_standard():
    # No clear template standard → image (adapt the reference), never a generic HTML dump.
    assert classify({}) == IMAGE
    assert classify({"ref": "01.jpg", "task": "adapt this"}) == IMAGE
