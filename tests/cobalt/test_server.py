"""Tests for local Cobalt provisioning (no real network/clone/install)."""
from unittest.mock import MagicMock, patch

import pytest

from social_media_agent.cobalt import server


def test_is_running_true_on_cobalt_json():
    resp = MagicMock()
    resp.status = 200
    resp.read.return_value = b'{"cobalt": {"version": "11"}, "git": {}}'
    cm = MagicMock()
    cm.__enter__.return_value = resp
    with patch("social_media_agent.cobalt.server.urllib.request.urlopen", return_value=cm):
        assert server.is_running("http://127.0.0.1:9000/") is True


def test_is_running_false_on_unreachable():
    with patch("social_media_agent.cobalt.server.urllib.request.urlopen", side_effect=OSError("refused")):
        assert server.is_running("http://127.0.0.1:9000/") is False


def test_is_running_false_on_non_cobalt_json():
    resp = MagicMock()
    resp.status = 200
    resp.read.return_value = b'{"hello": "world"}'
    cm = MagicMock()
    cm.__enter__.return_value = resp
    with patch("social_media_agent.cobalt.server.urllib.request.urlopen", return_value=cm):
        assert server.is_running("http://127.0.0.1:9000/") is False


def test_ensure_short_circuits_when_already_running():
    with patch("social_media_agent.cobalt.server.is_running", return_value=True), \
         patch("social_media_agent.cobalt.server.start") as mstart:
        assert server.ensure() is True
        mstart.assert_not_called()


def test_ensure_starts_when_not_running():
    with patch("social_media_agent.cobalt.server.is_running", return_value=False), \
         patch("social_media_agent.cobalt.server.start", return_value=4321) as mstart:
        assert server.ensure() is False
        mstart.assert_called_once()


def test_start_returns_zero_if_already_up():
    with patch("social_media_agent.cobalt.server.is_running", return_value=True):
        assert server.start(url="http://127.0.0.1:9000/") == 0


def test_require_raises_with_hint_when_tool_missing():
    with patch("social_media_agent.cobalt.server.shutil.which", return_value=None):
        with pytest.raises(server.CobaltSetupError, match="not found on PATH"):
            server._require("pnpm")


def test_api_url_normalizes_trailing_slash(monkeypatch):
    monkeypatch.setenv("COBALT_API_URL", "http://host:9000")
    assert server.api_url() == "http://host:9000/"
