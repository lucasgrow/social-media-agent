"""Tests for the engine registry (get_engine)."""
import pytest

from social_media_agent.engines import available_engines, get_engine, gemini_image, openai_gpt_image_2


def test_resolves_canonical_names():
    assert get_engine("openai_gpt_image_2") is openai_gpt_image_2
    assert get_engine("gemini_image") is gemini_image


def test_resolves_aliases():
    assert get_engine("openai") is openai_gpt_image_2
    assert get_engine("gemini") is gemini_image
    assert get_engine("nano-banana") is gemini_image


def test_unknown_engine_raises_with_options():
    with pytest.raises(ValueError, match="Unknown engine"):
        get_engine("midjourney")


def test_every_engine_exposes_common_surface():
    for name in available_engines():
        eng = get_engine(name)
        assert callable(eng.generate)
        assert callable(eng.edit)
        assert isinstance(eng.MAX_REFS, int)
        assert isinstance(eng.API_KEY_ENV, str) and eng.API_KEY_ENV
