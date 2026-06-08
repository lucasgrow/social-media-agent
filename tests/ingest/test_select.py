"""Tests for the deterministic ingest selector."""
from unittest.mock import patch

from social_media_agent.ingest.select import choose_ingestor, fetch


def test_ig_post_routes_to_cobalt():
    assert choose_ingestor("https://www.instagram.com/p/DNtjwK3ZH_l/") == "cobalt"
    assert choose_ingestor("https://instagram.com/p/ABC/?img_index=1") == "cobalt"


def test_ig_reel_and_others_route_to_ytdlp():
    assert choose_ingestor("https://www.instagram.com/reel/ABC/") == "yt_dlp"
    assert choose_ingestor("https://youtube.com/watch?v=abc") == "yt_dlp"
    assert choose_ingestor("https://x.com/u/status/1") == "yt_dlp"


def test_fetch_dispatches_ig_post_to_cobalt(tmp_path):
    with patch("social_media_agent.ingest.cobalt.fetch", return_value={"meta": {}, "media_files": []}) as mc:
        fetch("https://www.instagram.com/p/ABC/", tmp_path)
    mc.assert_called_once()


def test_fetch_dispatches_reel_to_ytdlp(tmp_path):
    with patch("social_media_agent.ingest.yt_dlp.fetch", return_value={"meta": {}, "media_files": []}) as my:
        fetch("https://www.instagram.com/reel/ABC/", tmp_path)
    my.assert_called_once()
