"""Tests for gemini_image engine adapter."""
import base64
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from social_media_agent.engines.gemini_image import MAX_REFS, edit, generate


def _resp(png_bytes: bytes = b"\x89PNG\r\n\x1a\nfake", *, error=None, no_image=False):
    fake = MagicMock()
    fake.status_code = 200
    fake.raise_for_status.return_value = None
    if error is not None:
        fake.json.return_value = {"error": {"message": error}}
    elif no_image:
        fake.json.return_value = {"candidates": [{"finishReason": "SAFETY", "content": {"parts": [{"text": "no"}]}}]}
    else:
        fake.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"inlineData": {"mimeType": "image/png", "data": base64.b64encode(png_bytes).decode()}}]}}
            ]
        }
    return fake


def _make_test_png(path: Path):
    Image.new("RGB", (10, 10), "white").save(path)


def test_generate_returns_image_bytes_on_success():
    want = b"\x89PNG\r\n\x1a\nfake-gen"
    with patch("social_media_agent.engines.gemini_image.requests.post", return_value=_resp(want)):
        result = generate(api_key="k", prompt="x")
    assert result == want


def test_generate_posts_to_generatecontent_endpoint():
    with patch("social_media_agent.engines.gemini_image.requests.post", return_value=_resp()) as mock_post:
        generate(api_key="k", prompt="x")
    assert ":generateContent" in mock_post.call_args[0][0]
    assert "gemini-3-pro-image-preview" in mock_post.call_args[0][0]


def test_generate_sends_api_key_header_and_image_config():
    with patch("social_media_agent.engines.gemini_image.requests.post", return_value=_resp()) as mock_post:
        generate(api_key="my-key", prompt="x", aspect_ratio="9:16", image_size="2K")
    headers = mock_post.call_args.kwargs["headers"]
    payload = mock_post.call_args.kwargs["json"]
    assert headers["x-goog-api-key"] == "my-key"
    assert payload["generationConfig"]["responseModalities"] == ["TEXT", "IMAGE"]
    assert payload["generationConfig"]["imageConfig"]["aspectRatio"] == "9:16"
    assert payload["contents"][0]["parts"][0]["text"] == "x"


def test_generate_raises_on_api_error():
    with patch("social_media_agent.engines.gemini_image.requests.post", return_value=_resp(error="bad")):
        with pytest.raises(RuntimeError, match="bad"):
            generate(api_key="k", prompt="x")


def test_generate_raises_when_no_image_returned():
    with patch("social_media_agent.engines.gemini_image.requests.post", return_value=_resp(no_image=True)):
        with pytest.raises(RuntimeError, match="no image"):
            generate(api_key="k", prompt="x")


def test_edit_sends_inline_data_parts_for_each_image():
    with tempfile.TemporaryDirectory() as tmp:
        imgs = []
        for i in range(3):
            p = Path(tmp) / f"{i}.png"
            _make_test_png(p)
            imgs.append(p)
        with patch("social_media_agent.engines.gemini_image.requests.post", return_value=_resp()) as mock_post:
            edit(api_key="k", prompt="combine", images=imgs)
        parts = mock_post.call_args.kwargs["json"]["contents"][0]["parts"]
        assert parts[0]["text"] == "combine"
        inline_parts = [p for p in parts if "inline_data" in p]
        assert len(inline_parts) == 3


def test_edit_accepts_up_to_max_refs():
    assert MAX_REFS == 14
    with tempfile.TemporaryDirectory() as tmp:
        imgs = []
        for i in range(MAX_REFS):
            p = Path(tmp) / f"{i}.png"
            _make_test_png(p)
            imgs.append(p)
        with patch("social_media_agent.engines.gemini_image.requests.post", return_value=_resp()) as mock_post:
            edit(api_key="k", prompt="x", images=imgs)
        parts = mock_post.call_args.kwargs["json"]["contents"][0]["parts"]
        assert len([p for p in parts if "inline_data" in p]) == MAX_REFS


def test_edit_raises_if_more_than_max_refs():
    with tempfile.TemporaryDirectory() as tmp:
        imgs = []
        for i in range(MAX_REFS + 1):
            p = Path(tmp) / f"{i}.png"
            _make_test_png(p)
            imgs.append(p)
        with pytest.raises(ValueError, match="at most 14"):
            edit(api_key="k", prompt="x", images=imgs)


def test_edit_raises_if_no_images():
    with pytest.raises(ValueError, match="at least 1"):
        edit(api_key="k", prompt="x", images=[])


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="requires GEMINI_API_KEY")
def test_generate_real_api_call():
    """Integration: real Gemini call returns valid image bytes."""
    result = generate(
        api_key=os.environ["GEMINI_API_KEY"],
        prompt="A simple cream-colored square. Plain background. No text.",
        aspect_ratio="1:1",
    )
    assert len(result) > 1000
