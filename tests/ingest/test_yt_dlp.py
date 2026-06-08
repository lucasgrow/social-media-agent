"""Tests for yt_dlp ingest adapter."""
import json
import shutil
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from social_media_agent.ingest.yt_dlp import fetch


def test_fetch_calls_yt_dlp_with_url(tmp_path):
    fake_meta = {"title": "Test", "uploader": "x", "id": "abc"}
    fake_result = MagicMock(returncode=0, stdout=json.dumps(fake_meta), stderr="")

    with patch("social_media_agent.ingest.yt_dlp.subprocess.run", return_value=fake_result) as mock_run:
        fetch(url="https://instagram.com/p/X/", output_dir=tmp_path)
    args = mock_run.call_args[0][0]
    assert "yt-dlp" in args[0] or args[0].endswith("yt-dlp")
    assert "https://instagram.com/p/X/" in args


def test_fetch_passes_output_dir(tmp_path):
    fake_meta = {"title": "T"}
    fake_result = MagicMock(returncode=0, stdout=json.dumps(fake_meta), stderr="")

    with patch("social_media_agent.ingest.yt_dlp.subprocess.run", return_value=fake_result) as mock_run:
        fetch(url="https://x.com/y/status/1", output_dir=tmp_path)
    args = mock_run.call_args[0][0]
    assert "-o" in args
    output_idx = args.index("-o")
    assert str(tmp_path) in args[output_idx + 1]


def test_fetch_returns_meta_dict(tmp_path):
    fake_meta = {"title": "My Post", "uploader": "alice", "id": "xyz123"}
    fake_result = MagicMock(returncode=0, stdout=json.dumps(fake_meta), stderr="")

    with patch("social_media_agent.ingest.yt_dlp.subprocess.run", return_value=fake_result):
        result = fetch(url="https://x.com/y/status/1", output_dir=tmp_path)
    assert result["meta"]["title"] == "My Post"
    assert result["meta"]["id"] == "xyz123"


def test_fetch_returns_media_files_list(tmp_path):
    (tmp_path / "abc.jpg").write_bytes(b"fake jpg")
    (tmp_path / "abc.mp4").write_bytes(b"fake mp4")

    fake_meta = {"id": "abc"}
    fake_result = MagicMock(returncode=0, stdout=json.dumps(fake_meta), stderr="")

    with patch("social_media_agent.ingest.yt_dlp.subprocess.run", return_value=fake_result):
        result = fetch(url="https://x.com/y/status/1", output_dir=tmp_path)
    names = sorted(p.name for p in result["media_files"])
    assert "abc.jpg" in names
    assert "abc.mp4" in names


def test_fetch_raises_on_yt_dlp_failure(tmp_path):
    fake_result = MagicMock(returncode=1, stdout="", stderr="ERROR: unsupported URL")

    with patch("social_media_agent.ingest.yt_dlp.subprocess.run", return_value=fake_result):
        with pytest.raises(RuntimeError, match="unsupported URL"):
            fetch(url="https://nope.com/x", output_dir=tmp_path)


@pytest.mark.skipif(shutil.which("yt-dlp") is None, reason="yt-dlp not installed")
def test_yt_dlp_binary_callable():
    """Integration: yt-dlp --version works (binary callable)."""
    result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
    assert result.returncode == 0
