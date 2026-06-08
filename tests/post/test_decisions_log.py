"""Tests for post.decisions_log."""
from social_media_agent.post.decisions_log import append_entry, init_log


def test_init_log_creates_decisions_md_with_header(tmp_path):
    log_path = tmp_path / "decisions.md"
    init_log(log_path, post_slug="01-my-post")
    text = log_path.read_text()
    assert "# Decisions log — 01-my-post" in text


def test_init_log_skips_if_file_exists(tmp_path):
    log_path = tmp_path / "decisions.md"
    log_path.write_text("# already here")
    init_log(log_path, post_slug="x")
    assert log_path.read_text() == "# already here"


def test_append_entry_writes_versioned_section(tmp_path):
    log_path = tmp_path / "decisions.md"
    init_log(log_path, post_slug="01-x")
    append_entry(log_path, version="v1", prompt="my prompt", note="generated cleanly")
    text = log_path.read_text()
    assert "## v1" in text
    assert "my prompt" in text
    assert "generated cleanly" in text


def test_append_entry_multiple_appends_in_order(tmp_path):
    log_path = tmp_path / "decisions.md"
    init_log(log_path, post_slug="01-x")
    append_entry(log_path, version="v1", prompt="p1")
    append_entry(log_path, version="v2", prompt="p2", note="user said tira o emblema")
    text = log_path.read_text()
    v1_pos = text.index("## v1")
    v2_pos = text.index("## v2")
    assert v1_pos < v2_pos
    assert "tira o emblema" in text


def test_append_entry_creates_log_if_missing(tmp_path):
    """append_entry on a non-existent log file should init it first."""
    log_path = tmp_path / "decisions.md"
    append_entry(log_path, version="v1", prompt="p", note="auto-init")
    assert log_path.is_file()
    text = log_path.read_text()
    assert "## v1" in text
