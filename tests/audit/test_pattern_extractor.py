"""Tests for audit.pattern_extractor."""
import json
from unittest.mock import patch

from social_media_agent.audit.pattern_extractor import extract_patterns


def test_extract_patterns_returns_dict_with_expected_keys():
    fake = json.dumps({
        "do_this": ["use Cormorant for info posts"],
        "avoid": ["solid colored blocks"],
        "voice_patterns": ["short hooks"],
        "engagement_signals": [],
    })
    with patch("social_media_agent.audit.pattern_extractor.extract_structured", return_value=fake):
        result = extract_patterns(api_key="sk", decisions_per_post=[])
    assert "do_this" in result
    assert "avoid" in result
    assert "voice_patterns" in result
    assert "engagement_signals" in result


def test_extract_patterns_passes_decisions_to_prompt():
    decisions_per_post = [
        {
            "post_slug": "01-a",
            "iterations": [
                {"version": "v1", "prompt": "p1", "note": "good"},
            ],
        }
    ]
    fake = '{"do_this": [], "avoid": [], "voice_patterns": [], "engagement_signals": []}'
    with patch("social_media_agent.audit.pattern_extractor.extract_structured", return_value=fake) as mock_ext:
        extract_patterns(api_key="sk", decisions_per_post=decisions_per_post)
    prompt = mock_ext.call_args.kwargs.get("prompt") or mock_ext.call_args.args[1]
    # Decisions content should appear in the prompt
    assert "01-a" in prompt
    assert "p1" in prompt


def test_extract_patterns_handles_empty_decisions():
    fake = '{"do_this": [], "avoid": [], "voice_patterns": [], "engagement_signals": []}'
    with patch("social_media_agent.audit.pattern_extractor.extract_structured", return_value=fake):
        result = extract_patterns(api_key="sk", decisions_per_post=[])
    assert result["do_this"] == []


def test_extract_patterns_handles_invalid_json_returns_defaults_with_raw():
    with patch("social_media_agent.audit.pattern_extractor.extract_structured", return_value="not json"):
        result = extract_patterns(api_key="sk", decisions_per_post=[])
    assert result["do_this"] == []
    assert result["avoid"] == []
    assert result["raw"] == "not json"
