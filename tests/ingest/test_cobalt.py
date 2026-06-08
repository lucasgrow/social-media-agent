"""Tests for the Cobalt ingest adapter (network mocked)."""
from unittest.mock import MagicMock, patch

import pytest

from social_media_agent.ingest.cobalt import CobaltError, fetch


def _api_resp(payload):
    m = MagicMock()
    m.json.return_value = payload
    m.status_code = 200
    return m


def _file_resp(blob, content_type="image/jpeg"):
    m = MagicMock()
    m.status_code = 200
    m.headers = {"Content-Type": content_type}
    m.iter_content.return_value = [blob]
    return m


def test_picker_downloads_every_carousel_asset(tmp_path):
    api = _api_resp({
        "status": "picker",
        "picker": [
            {"type": "photo", "url": "http://cobalt/1.jpg"},
            {"type": "photo", "url": "http://cobalt/2.jpg"},
            {"type": "photo", "url": "http://cobalt/3.jpg"},
        ],
    })
    with patch("social_media_agent.ingest.cobalt.requests.post", return_value=api), \
         patch("social_media_agent.ingest.cobalt.requests.get", return_value=_file_resp(b"jpg")) as mget:
        result = fetch("https://www.instagram.com/p/ABC/", tmp_path)

    assert len(result["media_files"]) == 3
    assert mget.call_count == 3
    assert all(p.exists() and p.suffix == ".jpg" for p in result["media_files"])
    assert result["meta"]["status"] == "picker"


def test_picker_first_downloads_only_one(tmp_path):
    api = _api_resp({
        "status": "picker",
        "picker": [
            {"type": "photo", "url": "http://cobalt/1.jpg"},
            {"type": "photo", "url": "http://cobalt/2.jpg"},
        ],
    })
    with patch("social_media_agent.ingest.cobalt.requests.post", return_value=api), \
         patch("social_media_agent.ingest.cobalt.requests.get", return_value=_file_resp(b"jpg")):
        from social_media_agent.ingest.cobalt import fetch as f
        result = f("https://www.instagram.com/p/ABC/", tmp_path, picker="first")
    assert len(result["media_files"]) == 1


def test_redirect_downloads_single_file(tmp_path):
    api = _api_resp({"status": "redirect", "url": "http://cobalt/v.mp4"})
    with patch("social_media_agent.ingest.cobalt.requests.post", return_value=api), \
         patch("social_media_agent.ingest.cobalt.requests.get", return_value=_file_resp(b"mp4", "video/mp4")):
        result = fetch("https://www.instagram.com/reel/ABC/", tmp_path)
    assert len(result["media_files"]) == 1
    assert result["media_files"][0].suffix == ".mp4"


def test_error_status_raises(tmp_path):
    api = _api_resp({"status": "error", "error": {"code": "fetch.fail"}})
    with patch("social_media_agent.ingest.cobalt.requests.post", return_value=api):
        with pytest.raises(CobaltError, match="error"):
            fetch("https://www.instagram.com/p/ABC/", tmp_path)


def test_unreachable_api_raises_with_hint(tmp_path):
    import requests as _rq

    with patch("social_media_agent.ingest.cobalt.requests.post", side_effect=_rq.ConnectionError("refused")):
        with pytest.raises(CobaltError, match="Could not reach Cobalt"):
            fetch("https://www.instagram.com/p/ABC/", tmp_path)
