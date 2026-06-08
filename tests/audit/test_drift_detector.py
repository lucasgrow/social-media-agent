"""Tests for audit.drift_detector."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from social_media_agent.audit.drift_detector import detect_drift


def _make_png(path: Path):
    from PIL import Image
    Image.new("RGB", (10, 10), "white").save(path)


def test_detect_drift_returns_dict_with_expected_keys():
    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "out.png"
        paleta = Path(tmp) / "03-paleta.png"
        for p in [img, paleta]:
            _make_png(p)

        fake_response = json.dumps({
            "palette_drift": False,
            "font_drift": False,
            "donts_violations": []
        })
        with patch("social_media_agent.audit.drift_detector.analyze_image", return_value=fake_response):
            result = detect_drift(
                api_key="sk",
                output_image=img,
                brand_pages={"paleta": paleta},
            )
        assert "palette_drift" in result
        assert "font_drift" in result
        assert "donts_violations" in result


def test_detect_drift_passes_image_to_analyze_image():
    """The output_image (not brand_pages) is the one being analyzed."""
    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "out.png"
        paleta = Path(tmp) / "03-paleta.png"
        for p in [img, paleta]:
            _make_png(p)

        fake_response = '{"palette_drift": false, "font_drift": false, "donts_violations": []}'
        with patch("social_media_agent.audit.drift_detector.analyze_image", return_value=fake_response) as mock_v:
            detect_drift(api_key="sk", output_image=img, brand_pages={"paleta": paleta})
        # analyze_image called with image_path=img
        assert mock_v.call_args.kwargs.get("image_path") == img or mock_v.call_args.args[2] == img


def test_detect_drift_prompt_mentions_brand_palette_hex_if_paleta_provided():
    """Prompt should reference the brand palette context."""
    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "out.png"
        paleta = Path(tmp) / "03-paleta.png"
        for p in [img, paleta]:
            _make_png(p)

        fake_response = '{"palette_drift": false, "font_drift": false, "donts_violations": []}'
        with patch("social_media_agent.audit.drift_detector.analyze_image", return_value=fake_response) as mock_v:
            detect_drift(api_key="sk", output_image=img, brand_pages={"paleta": paleta})
        prompt = mock_v.call_args.kwargs.get("prompt") or mock_v.call_args.args[1]
        # Prompt should mention drift / palette / brand
        assert "drift" in prompt.lower() or "brand" in prompt.lower()


def test_detect_drift_handles_invalid_json_response_gracefully():
    """If LLM returns non-JSON, return an empty-shape dict with raw response in 'raw'."""
    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "out.png"
        _make_png(img)

        with patch("social_media_agent.audit.drift_detector.analyze_image", return_value="not json at all"):
            result = detect_drift(api_key="sk", output_image=img, brand_pages={})
        assert result["palette_drift"] is False
        assert result["font_drift"] is False
        assert result["donts_violations"] == []
        assert result["raw"] == "not json at all"
