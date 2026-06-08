"""Tests for utils.env."""
import os

import pytest

from social_media_agent.utils.env import find_repo_root, load_env


def test_load_env_parses_simple_key_value(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\nBAZ=qux\n")
    result = load_env(env)
    assert result["FOO"] == "bar"
    assert result["BAZ"] == "qux"


def test_load_env_skips_comments_and_blank_lines(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# a comment\n\nFOO=bar\n  # indented comment\n")
    result = load_env(env)
    assert result == {"FOO": "bar"}


def test_load_env_strips_surrounding_quotes(tmp_path):
    env = tmp_path / ".env"
    env.write_text('FOO="quoted"\nBAR=\'single\'\nBAZ=plain\n')
    result = load_env(env)
    assert result["FOO"] == "quoted"
    assert result["BAR"] == "single"
    assert result["BAZ"] == "plain"


def test_load_env_preserves_equals_in_value(tmp_path):
    """KEY=value=with=equals must keep all equals in value."""
    env = tmp_path / ".env"
    env.write_text("URL=https://api.example.com/v1/?a=1&b=2\n")
    result = load_env(env)
    assert result["URL"] == "https://api.example.com/v1/?a=1&b=2"


def test_load_env_missing_file_returns_empty_dict(tmp_path):
    """No raise on missing — calling code may not have .env yet."""
    result = load_env(tmp_path / "nope.env")
    assert result == {}


def test_load_env_into_os_environ(tmp_path, monkeypatch):
    """When inject=True, values are setdefault'd into os.environ."""
    env = tmp_path / ".env"
    env.write_text("UNIQ_TEST_KEY_X42=hello\n")
    monkeypatch.delenv("UNIQ_TEST_KEY_X42", raising=False)
    load_env(env, inject=True)
    assert os.environ["UNIQ_TEST_KEY_X42"] == "hello"


def test_load_env_inject_does_not_override_existing(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("ALREADY_SET=fromfile\n")
    monkeypatch.setenv("ALREADY_SET", "fromshell")
    load_env(env, inject=True)
    assert os.environ["ALREADY_SET"] == "fromshell"


def test_find_repo_root_walks_up_to_pyproject(tmp_path):
    """find_repo_root walks up from start_path until it finds pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    sub = tmp_path / "a" / "b" / "c"
    sub.mkdir(parents=True)
    result = find_repo_root(sub)
    assert result == tmp_path


def test_find_repo_root_raises_if_no_pyproject(tmp_path):
    with pytest.raises(FileNotFoundError, match="pyproject.toml"):
        find_repo_root(tmp_path)
