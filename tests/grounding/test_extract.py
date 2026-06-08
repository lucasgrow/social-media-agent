"""Tests for grounding.extract."""
from unittest.mock import patch

from social_media_agent.grounding import parse_json_lenient
from social_media_agent.grounding.extract import extract_subjects


def _patch_llm(response: str):
    return patch("social_media_agent.grounding.extract.extract_structured", return_value=response)


def test_parses_subject_array():
    resp = '[{"name": "Golden Gate Bridge", "kind": "place", "search_query": "Golden Gate Bridge photo", "why": "post subject"}]'
    with _patch_llm(resp):
        subjects = extract_subjects("post about the Golden Gate Bridge", api_key="k")
    assert len(subjects) == 1
    assert subjects[0]["name"] == "Golden Gate Bridge"
    assert subjects[0]["kind"] == "place"
    assert subjects[0]["search_query"] == "Golden Gate Bridge photo"


def test_tolerates_code_fenced_json():
    resp = '```json\n[{"name": "Cristo Redentor", "kind": "place"}]\n```'
    with _patch_llm(resp):
        subjects = extract_subjects("x", api_key="k")
    assert subjects[0]["name"] == "Cristo Redentor"
    assert subjects[0]["kind"] == "place"


def test_empty_array_when_nothing_to_ground():
    with _patch_llm("[]"):
        assert extract_subjects("abstract typographic post", api_key="k") == []


def test_non_list_response_yields_empty():
    with _patch_llm("I could not find anything to ground."):
        assert extract_subjects("x", api_key="k") == []


def test_unknown_kind_normalized_to_other():
    with _patch_llm('[{"name": "X", "kind": "monument"}]'):
        assert extract_subjects("x", api_key="k")[0]["kind"] == "other"


def test_items_without_name_are_dropped():
    with _patch_llm('[{"kind": "person"}, {"name": "Real Person", "kind": "person"}]'):
        subjects = extract_subjects("x", api_key="k")
    assert [s["name"] for s in subjects] == ["Real Person"]


def test_search_query_defaults_to_name():
    with _patch_llm('[{"name": "Igreja Matriz"}]'):
        assert extract_subjects("x", api_key="k")[0]["search_query"] == "Igreja Matriz"


def test_parse_json_lenient_handles_prose_wrapped_json():
    assert parse_json_lenient('here you go: [{"a":1}] done') == [{"a": 1}]
    assert parse_json_lenient("not json") is None
