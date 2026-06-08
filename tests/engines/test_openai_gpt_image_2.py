"""Tests for openai_gpt_image_2 engine adapter."""
import base64
import os
from unittest.mock import MagicMock, patch

import pytest

from social_media_agent.engines.openai_gpt_image_2 import generate


def test_generate_returns_png_bytes_on_success():
    fake_png_bytes = b"\x89PNG\r\n\x1a\nfake"
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "data": [{"b64_json": base64.b64encode(fake_png_bytes).decode()}]
    }
    fake_response.raise_for_status.return_value = None

    with patch("social_media_agent.engines.openai_gpt_image_2.requests.post", return_value=fake_response):
        result = generate(
            api_key="sk-test",
            prompt="test prompt",
            size="1024x1024",
            quality="high",
        )

    assert result == fake_png_bytes


def test_generate_posts_to_correct_endpoint():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"data": [{"b64_json": base64.b64encode(b"x").decode()}]}
    fake_response.raise_for_status.return_value = None

    with patch("social_media_agent.engines.openai_gpt_image_2.requests.post", return_value=fake_response) as mock_post:
        generate(api_key="sk-test", prompt="x", size="1024x1024", quality="high")

    assert "/v1/images/generations" in mock_post.call_args[0][0]


def test_generate_sends_authorization_header():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"data": [{"b64_json": base64.b64encode(b"x").decode()}]}
    fake_response.raise_for_status.return_value = None

    with patch("social_media_agent.engines.openai_gpt_image_2.requests.post", return_value=fake_response) as mock_post:
        generate(api_key="sk-test-key", prompt="x", size="1024x1024", quality="high")

    headers = mock_post.call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer sk-test-key"


def test_generate_sends_expected_payload():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"data": [{"b64_json": base64.b64encode(b"x").decode()}]}
    fake_response.raise_for_status.return_value = None

    with patch("social_media_agent.engines.openai_gpt_image_2.requests.post", return_value=fake_response) as mock_post:
        generate(
            api_key="sk-test",
            prompt="my prompt",
            size="1024x1280",
            quality="high",
        )

    payload = mock_post.call_args.kwargs["json"]
    assert payload["prompt"] == "my prompt"
    assert payload["size"] == "1024x1280"
    assert payload["quality"] == "high"
    assert payload["model"].startswith("gpt-image")
    assert payload["n"] == 1


def test_generate_raises_on_api_error():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"error": {"message": "bad prompt"}}
    fake_response.raise_for_status.return_value = None

    with patch("social_media_agent.engines.openai_gpt_image_2.requests.post", return_value=fake_response):
        with pytest.raises(RuntimeError, match="bad prompt"):
            generate(api_key="sk-test", prompt="x", size="1024x1024", quality="high")


@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="requires OPENAI_API_KEY")
def test_generate_real_api_call():
    """Integration: real OpenAI call returns valid PNG bytes."""
    result = generate(
        api_key=os.environ["OPENAI_API_KEY"],
        prompt="A simple cream-colored square. No text. Plain background.",
        size="1024x1024",
        quality="high",
    )
    assert result[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(result) > 1000


import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

from PIL import Image  # noqa: E402

from social_media_agent.engines.openai_gpt_image_2 import edit  # noqa: E402


def _make_test_png(path: Path):
    Image.new("RGB", (10, 10), "white").save(path)


def test_edit_returns_png_bytes_on_success():
    fake_png = b"\x89PNG\r\n\x1a\nfake-edited"
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"data": [{"b64_json": base64.b64encode(fake_png).decode()}]}
    fake_response.raise_for_status.return_value = None

    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "in.png"
        _make_test_png(img)
        with patch("social_media_agent.engines.openai_gpt_image_2.requests.post", return_value=fake_response):
            result = edit(
                api_key="sk-test",
                prompt="edit this",
                images=[img],
                size="1024x1024",
                quality="high",
            )
    assert result == fake_png


def test_edit_posts_to_correct_endpoint():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"data": [{"b64_json": base64.b64encode(b"x").decode()}]}
    fake_response.raise_for_status.return_value = None

    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "in.png"
        _make_test_png(img)
        with patch("social_media_agent.engines.openai_gpt_image_2.requests.post", return_value=fake_response) as mock_post:
            edit(api_key="sk-test", prompt="x", images=[img], size="1024x1024", quality="high")
    assert "/v1/images/edits" in mock_post.call_args[0][0]


def test_edit_accepts_multiple_images_up_to_5():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"data": [{"b64_json": base64.b64encode(b"x").decode()}]}
    fake_response.raise_for_status.return_value = None

    with tempfile.TemporaryDirectory() as tmp:
        imgs = []
        for i in range(5):
            p = Path(tmp) / f"{i}.png"
            _make_test_png(p)
            imgs.append(p)
        with patch("social_media_agent.engines.openai_gpt_image_2.requests.post", return_value=fake_response) as mock_post:
            edit(api_key="sk-test", prompt="x", images=imgs, size="1024x1024", quality="high")
        files_arg = mock_post.call_args.kwargs.get("files") or []
        image_files = [f for f in files_arg if f[0] == "image[]"]
        assert len(image_files) == 5


def test_edit_raises_if_more_than_5_images():
    with tempfile.TemporaryDirectory() as tmp:
        imgs = []
        for i in range(6):
            p = Path(tmp) / f"{i}.png"
            _make_test_png(p)
            imgs.append(p)
        with pytest.raises(ValueError, match="at most 5"):
            edit(api_key="sk-test", prompt="x", images=imgs, size="1024x1024", quality="high")


def test_edit_raises_if_no_images():
    with pytest.raises(ValueError, match="at least 1"):
        edit(api_key="sk-test", prompt="x", images=[], size="1024x1024", quality="high")
