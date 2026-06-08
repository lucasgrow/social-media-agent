"""Tests for grounding.ground (ref persistence + manifest)."""
import json
import tempfile
from pathlib import Path

from PIL import Image

from social_media_agent.grounding.ground import (
    collect_grounded_refs,
    register_ref,
    subject_slug,
)

SUBJECT = {"name": "São Paulo Cathedral", "kind": "landmark", "search_query": "q", "why": "post subject"}


def _png(path: Path):
    Image.new("RGB", (8, 8), "white").save(path)


def test_subject_slug_strips_accents():
    assert subject_slug("São Paulo Cathedral") == "sao-paulo-cathedral"


def test_register_copies_file_and_writes_manifest():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        post_dir = tmp / "post"
        post_dir.mkdir()
        src = tmp / "ref.png"
        _png(src)

        dest = register_ref(post_dir, SUBJECT, src, source="user", score=0.9)

        assert dest.is_file()
        assert "sao-paulo-cathedral" in str(dest)
        manifest = json.loads((post_dir / "refs" / "grounded" / "grounding.json").read_text())
        assert len(manifest) == 1
        assert manifest[0]["subject"] == "São Paulo Cathedral"
        assert manifest[0]["source"] == "user"
        assert manifest[0]["score"] == 0.9


def test_multiple_refs_same_subject_dedup_names():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        post_dir = tmp / "post"
        post_dir.mkdir()
        for i in range(3):
            src = tmp / f"r{i}.png"
            _png(src)
            register_ref(post_dir, SUBJECT, src, source="web")
        refs = collect_grounded_refs(post_dir)
        assert len(refs) == 3
        assert len({r.name for r in refs}) == 3  # unique filenames


def test_collect_empty_when_no_refs():
    with tempfile.TemporaryDirectory() as tmp:
        assert collect_grounded_refs(Path(tmp)) == []


def test_collect_excludes_manifest_json():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        post_dir = tmp / "post"
        post_dir.mkdir()
        src = tmp / "r.png"
        _png(src)
        register_ref(post_dir, SUBJECT, src, source="user")
        refs = collect_grounded_refs(post_dir)
        assert all(r.suffix.lower() != ".json" for r in refs)
        assert len(refs) == 1
