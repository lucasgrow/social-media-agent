"""Tests for grounding.search (Serper, optional)."""
from unittest.mock import MagicMock, patch

import pytest

from social_media_agent.grounding import search


def test_serper_available_reflects_env(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    assert search.serper_available() is False
    monkeypatch.setenv("SERPER_API_KEY", "key123")
    assert search.serper_available() is True


def test_search_raises_without_key(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SERPER_API_KEY"):
        search.serper_image_search("Golden Gate Bridge")


def test_search_returns_image_urls(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "key123")
    fake = MagicMock()
    fake.raise_for_status.return_value = None
    fake.json.return_value = {"images": [{"imageUrl": "https://a/1.jpg"}, {"imageUrl": "https://a/2.jpg"}]}
    with patch("social_media_agent.grounding.search.requests.post", return_value=fake) as m:
        urls = search.serper_image_search("Golden Gate Bridge", n=5)
    assert urls == ["https://a/1.jpg", "https://a/2.jpg"]
    assert m.call_args.kwargs["headers"]["X-API-KEY"] == "key123"


def test_search_respects_n(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")
    fake = MagicMock()
    fake.raise_for_status.return_value = None
    fake.json.return_value = {"images": [{"imageUrl": f"u{i}"} for i in range(10)]}
    with patch("social_media_agent.grounding.search.requests.post", return_value=fake):
        urls = search.serper_image_search("q", n=3)
    assert len(urls) == 3
