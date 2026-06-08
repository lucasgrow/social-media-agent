"""Tests for audit.decisions_parser."""
from datetime import datetime

from social_media_agent.audit.decisions_parser import parse_decisions

# Reuse the existing decisions_log helpers to build fixtures
from social_media_agent.post.decisions_log import append_entry, init_log


def test_parse_decisions_returns_list_of_entries(tmp_path):
    log = tmp_path / "decisions.md"
    init_log(log, post_slug="01-test")
    append_entry(log, version="v1", prompt="hello", note="ok")

    result = parse_decisions(log)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["version"] == "v1"
    assert result[0]["prompt"] == "hello"
    assert result[0]["note"] == "ok"


def test_parse_decisions_multiple_entries_in_order(tmp_path):
    log = tmp_path / "decisions.md"
    init_log(log, post_slug="01-test")
    append_entry(log, version="v1", prompt="first", note="ok")
    append_entry(log, version="v2", prompt="second", note="needed edit")
    append_entry(log, version="v3", prompt="third")

    result = parse_decisions(log)
    assert [e["version"] for e in result] == ["v1", "v2", "v3"]
    assert result[0]["note"] == "ok"
    assert result[2]["note"] == ""  # no note → empty string


def test_parse_decisions_extracts_timestamp(tmp_path):
    log = tmp_path / "decisions.md"
    init_log(log, post_slug="01-test")
    append_entry(log, version="v1", prompt="p", note="n")

    result = parse_decisions(log)
    # Timestamp is YYYY-MM-DD HH:MM:SS format
    assert "timestamp" in result[0]
    datetime.strptime(result[0]["timestamp"], "%Y-%m-%d %H:%M:%S")


def test_parse_decisions_empty_log_returns_empty_list(tmp_path):
    log = tmp_path / "decisions.md"
    init_log(log, post_slug="01-test")
    result = parse_decisions(log)
    assert result == []


def test_parse_decisions_missing_file_returns_empty_list(tmp_path):
    result = parse_decisions(tmp_path / "nonexistent.md")
    assert result == []
