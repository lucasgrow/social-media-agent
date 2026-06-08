"""Tests for engines.spec.resolve_gen_kwargs."""
from social_media_agent.engines.spec import resolve_gen_kwargs


def test_openai_returns_pixel_size_and_quality():
    kw = resolve_gen_kwargs("openai_gpt_image_2", "feed_4x5")
    assert kw == {"size": "1024x1280", "quality": "high"}


def test_openai_alias_and_other_formats():
    assert resolve_gen_kwargs("openai", "feed_1x1")["size"] == "1024x1024"
    assert resolve_gen_kwargs("openai", "story_9x16_still")["size"] == "1024x1536"


def test_gemini_returns_aspect_ratio_and_image_size():
    kw = resolve_gen_kwargs("gemini_image", "feed_4x5")
    assert kw == {"aspect_ratio": "4:5", "image_size": "2K"}


def test_gemini_alias_and_vertical_format():
    kw = resolve_gen_kwargs("gemini", "story_9x16_still")
    assert kw["aspect_ratio"] == "9:16"


def test_unknown_format_falls_back():
    assert resolve_gen_kwargs("openai", "weird")["size"] == "1024x1280"
    assert resolve_gen_kwargs("gemini", "weird")["aspect_ratio"] == "4:5"
