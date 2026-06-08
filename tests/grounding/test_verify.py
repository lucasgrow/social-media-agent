"""Tests for grounding.verify."""
from pathlib import Path
from unittest.mock import patch

from social_media_agent.grounding.verify import verify_ref

SUBJECT = {"name": "Golden Gate Bridge", "kind": "landmark", "why": "post subject"}


def _patch_vision(response: str):
    return patch("social_media_agent.grounding.verify.analyze_image", return_value=response)


def test_match_true_when_model_confident():
    with _patch_vision('{"match": true, "score": 0.92, "reason": "clearly her"}'):
        v = verify_ref(SUBJECT, Path("/tmp/x.png"), api_key="k")
    assert v["match"] is True
    assert v["score"] == 0.92


def test_low_score_rejected_even_if_match_true():
    with _patch_vision('{"match": true, "score": 0.4, "reason": "maybe"}'):
        v = verify_ref(SUBJECT, Path("/tmp/x.png"), api_key="k", min_score=0.6)
    assert v["match"] is False


def test_match_false_passthrough():
    with _patch_vision('{"match": false, "score": 0.1, "reason": "different person"}'):
        v = verify_ref(SUBJECT, Path("/tmp/x.png"), api_key="k")
    assert v["match"] is False


def test_unparseable_verdict_is_non_matching():
    with _patch_vision("it looks kind of like her maybe"):
        v = verify_ref(SUBJECT, Path("/tmp/x.png"), api_key="k")
    assert v["match"] is False
    assert v["score"] == 0.0


def test_subject_context_in_prompt():
    with _patch_vision('{"match": true, "score": 0.8}') as m:
        verify_ref(SUBJECT, Path("/tmp/x.png"), api_key="k")
    sent_prompt = m.call_args.kwargs["prompt"]
    assert "Golden Gate Bridge" in sent_prompt
    assert "landmark" in sent_prompt
