"""Tests for image_renderer."""
from social_media_agent.render.image_renderer import save


def test_save_writes_bytes_to_path(tmp_path):
    data = b"\x89PNG\r\n\x1a\nfake-png-content"
    out = tmp_path / "feed.png"
    save(data, out)
    assert out.read_bytes() == data


def test_save_creates_parent_dirs_if_missing(tmp_path):
    data = b"x"
    out = tmp_path / "outputs" / "v1" / "feed.png"
    save(data, out)
    assert out.exists()
    assert out.read_bytes() == data


def test_save_overwrites_existing_file(tmp_path):
    out = tmp_path / "f.png"
    out.write_bytes(b"old")
    save(b"new", out)
    assert out.read_bytes() == b"new"


import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from social_media_agent.render.image_renderer import preview_grid  # noqa: E402


def test_preview_grid_returns_pillow_image(tmp_path):
    slides = []
    for i in range(2):
        p = tmp_path / f"{i}.png"
        Image.new("RGB", (100, 100), "red").save(p)
        slides.append(p)
    out = preview_grid(slides, cols=2)
    assert isinstance(out, Image.Image)


def test_preview_grid_6_slides_round_trip(tmp_path):
    slides = []
    for i in range(6):
        p = tmp_path / f"{i}.png"
        Image.new("RGB", (100, 200), "blue").save(p)
        slides.append(p)
    out = preview_grid(slides, cols=3)
    assert out.width > 0
    assert out.height > 0
    saved = tmp_path / "preview.png"
    out.save(saved)
    reopened = Image.open(saved)
    assert reopened.size == out.size


def test_preview_grid_empty_list_raises():
    with pytest.raises(ValueError, match="at least 1"):
        preview_grid([], cols=2)
