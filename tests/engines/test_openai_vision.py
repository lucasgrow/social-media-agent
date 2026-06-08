"""Tests for openai_vision adapter."""
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from social_media_agent.engines.openai_vision import analyze_image, extract_structured


def _make_test_png(path: Path):
    Image.new("RGB", (10, 10), "white").save(path)


def test_analyze_image_returns_text_content():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": "this image is on-brand"}}]
    }
    fake_response.raise_for_status.return_value = None

    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "in.png"
        _make_test_png(img)
        with patch("social_media_agent.engines.openai_vision.requests.post", return_value=fake_response):
            result = analyze_image(api_key="sk-test", prompt="is this on brand?", image_path=img)
    assert result == "this image is on-brand"


def test_analyze_image_posts_to_chat_completions():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    fake_response.raise_for_status.return_value = None

    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "in.png"
        _make_test_png(img)
        with patch("social_media_agent.engines.openai_vision.requests.post", return_value=fake_response) as mock_post:
            analyze_image(api_key="sk", prompt="x", image_path=img)
    assert "/v1/chat/completions" in mock_post.call_args[0][0]


def test_analyze_image_payload_includes_base64_image():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    fake_response.raise_for_status.return_value = None

    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "in.png"
        _make_test_png(img)
        with patch("social_media_agent.engines.openai_vision.requests.post", return_value=fake_response) as mock_post:
            analyze_image(api_key="sk", prompt="x", image_path=img)
    payload = mock_post.call_args.kwargs["json"]
    messages = payload["messages"]
    # User message has multimodal content: text + image_url
    user_content = messages[-1]["content"]
    assert isinstance(user_content, list)
    types = [c["type"] for c in user_content]
    assert "text" in types
    assert "image_url" in types
    image_url = next(c for c in user_content if c["type"] == "image_url")
    assert image_url["image_url"]["url"].startswith("data:image/png;base64,")


def test_analyze_image_raises_on_api_error():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"error": {"message": "rate limited"}}
    fake_response.raise_for_status.return_value = None

    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "in.png"
        _make_test_png(img)
        with patch("social_media_agent.engines.openai_vision.requests.post", return_value=fake_response):
            with pytest.raises(RuntimeError, match="rate limited"):
                analyze_image(api_key="sk", prompt="x", image_path=img)


def test_extract_structured_returns_text_content():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": '{"do_this": ["pattern1"]}'}}]
    }
    fake_response.raise_for_status.return_value = None

    with patch("social_media_agent.engines.openai_vision.requests.post", return_value=fake_response):
        result = extract_structured(api_key="sk", prompt="extract patterns")
    assert result == '{"do_this": ["pattern1"]}'


def test_extract_structured_payload_text_only_messages():
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    fake_response.raise_for_status.return_value = None

    with patch("social_media_agent.engines.openai_vision.requests.post", return_value=fake_response) as mock_post:
        extract_structured(api_key="sk", prompt="my prompt")
    payload = mock_post.call_args.kwargs["json"]
    # Text-only — user content is a plain string, not multimodal list
    assert isinstance(payload["messages"][-1]["content"], str)
    assert payload["messages"][-1]["content"] == "my prompt"


@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="requires OPENAI_API_KEY")
def test_analyze_image_real_api_call():
    """Integration: real OpenAI vision call returns non-empty text."""
    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "test.png"
        Image.new("RGB", (200, 200), "red").save(img)
        result = analyze_image(
            api_key=os.environ["OPENAI_API_KEY"],
            prompt="What color is this image? Reply with one word.",
            image_path=img,
        )
    assert len(result) > 0
    assert "red" in result.lower()
