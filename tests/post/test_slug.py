"""Tests for post.slug.auto_slug."""
from social_media_agent.post.slug import auto_slug


def test_auto_slug_from_title():
    assert auto_slug(title="My Awesome Post!") == "my-awesome-post"


def test_auto_slug_strips_punctuation_and_lowercases():
    assert auto_slug(title="Café com IA: edição #3") == "cafe-com-ia-edicao-3"


def test_auto_slug_collapses_spaces_to_single_dash():
    assert auto_slug(title="hello    world") == "hello-world"


def test_auto_slug_truncates_long_titles_to_60_chars():
    title = "a " * 100
    result = auto_slug(title=title)
    assert len(result) <= 60


def test_auto_slug_strips_leading_trailing_dashes():
    assert auto_slug(title="--hello world--") == "hello-world"


def test_auto_slug_falls_back_to_url_path_if_no_title():
    assert auto_slug(title=None, url="https://www.instagram.com/p/DXyz123/") == "dxyz123"


def test_auto_slug_falls_back_to_post_if_no_title_no_url():
    assert auto_slug(title=None, url=None) == "post"
