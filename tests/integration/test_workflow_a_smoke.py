"""Integration smoke — Workflow A bootstrap + materialize on example-brand."""
import json
import shutil
from pathlib import Path

from social_media_agent.post.bootstrap import bootstrap_post
from social_media_agent.post.caption import create_caption_skeleton
from social_media_agent.post.decisions_log import append_entry, init_log
from social_media_agent.post.discover_profile import discover_profile
from social_media_agent.post.materialize import materialize_craft_py
from social_media_agent.post.slug import auto_slug

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROFILES_DIR = REPO_ROOT / "profiles"
TEMPLATE_DIR = REPO_ROOT / "src" / "social_media_agent" / "templates"


def test_workflow_a_end_to_end_against_example_brand(tmp_path, monkeypatch):
    """Simulate: user pastes link → skill ingests (mocked) → bootstraps → materializes → logs.

    Does NOT call OpenAI. Verifies the skill helper chain composes correctly against the
    example-brand profile.
    """
    # Use a tmp copy of profiles so we don't pollute the real example-brand
    profiles_copy = tmp_path / "profiles"
    shutil.copytree(PROFILES_DIR / "example-brand", profiles_copy / "example-brand")

    # 1. Profile discovery
    profile_dir = discover_profile(profiles_dir=profiles_copy, name="example-brand")
    assert profile_dir.name == "example-brand"

    # 2. Auto-slug from a fake title
    slug = auto_slug(title="Smoke test — integration A", url=None)
    assert slug == "smoke-test-integration-a"

    # 3. Bootstrap post (no real source files — empty ingest)
    fake_source = tmp_path / "fake-ingest.jpg"
    fake_source.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    result = bootstrap_post(
        profile_dir=profile_dir,
        slug=slug,
        year_month="2026-99",  # use a sentinel month so we don't collide with real posts
        format_="feed_4x5",
        engine="openai_gpt_image_2",
        source_url="https://example.com/source",
        source_files=[fake_source],
        source_meta={"title": "Smoke test", "id": "abc"},
    )

    post_dir = result["post_dir"]
    assert post_dir.is_dir()
    assert (post_dir / "source" / "fake-ingest.jpg").is_file()
    assert (post_dir / "source" / "original-link.txt").read_text().strip() == "https://example.com/source"
    assert json.loads((post_dir / "source" / "meta.json").read_text())["id"] == "abc"
    assert (post_dir / "brief.md").is_file()

    # 4. Materialize craft.py
    craft = materialize_craft_py(post_dir, template_dir=TEMPLATE_DIR)
    craft_text = craft.read_text()
    assert craft.is_file()
    assert "example-brand" in craft_text
    assert 'FORMAT = "feed_4x5"' in craft_text  # size resolved at runtime via resolve_gen_kwargs

    # 5. Init decisions log + append v1 entry
    init_log(post_dir / "decisions.md", post_slug=post_dir.name)
    append_entry(post_dir / "decisions.md", version="v1", prompt="(would be the prompt)", note="smoke")
    log_text = (post_dir / "decisions.md").read_text()
    assert "## v1" in log_text
    assert "smoke" in log_text

    # 6. Create caption skeleton
    caption = create_caption_skeleton(post_dir=post_dir, profile_dir=profile_dir)
    assert caption.is_file()
    assert "@examplebrand" in caption.read_text()


def test_workflow_a_smoke_does_not_leak_to_real_profiles_dir():
    """Sanity: the smoke test uses tmp_path, never touches real profiles/."""
    # If this test ever fails, prior runs may have leaked — manual cleanup needed
    real_smoke_dir = PROFILES_DIR / "example-brand" / "posts" / "2026-99"
    assert not real_smoke_dir.exists(), (
        "Real profile has 2026-99 directory — smoke test leaked. Clean it up: "
        f"trash {real_smoke_dir}"
    )
