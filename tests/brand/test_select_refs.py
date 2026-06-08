"""Tests for prompt_builder.select_refs (ref priority + cap + dedup)."""
from pathlib import Path

from social_media_agent.brand.prompt_builder import build_prompt, select_refs

G = [Path("/g/g1.png"), Path("/g/g2.png"), Path("/g/g3.png"), Path("/g/g4.png")]
S = [Path("/s/src.png")]
B = [Path("/b/p1.png"), Path("/b/p2.png"), Path("/b/p3.png")]


def test_priority_order_grounded_then_source_then_brand():
    refs = select_refs(grounded=G[:1], source=S, brand_pages=B)
    assert refs == [G[0], S[0], B[0], B[1], B[2]]


def test_grounded_capped_by_max_grounded():
    refs = select_refs(grounded=G, source=[], brand_pages=[], max_grounded=3)
    assert refs == G[:3]


def test_limit_caps_total_for_tight_budget():
    refs = select_refs(grounded=G[:2], source=S, brand_pages=B, limit=5)
    assert len(refs) == 5
    assert refs[0] == G[0] and refs[1] == G[1]  # grounded survives the cap


def test_dedup_preserves_first_occurrence():
    dup = Path("/b/p1.png")
    refs = select_refs(grounded=[dup], source=[], brand_pages=B)
    assert refs.count(dup) == 1
    assert refs == [dup, B[1], B[2]]


def test_no_limit_keeps_all():
    refs = select_refs(grounded=[], source=S, brand_pages=B)
    assert refs == S + B


def test_build_prompt_threads_grounded_and_limit():
    text, refs = build_prompt(
        task="t", design={}, voice={}, brand_pages=B, extra_refs=S,
        grounded_refs=G[:2], ref_limit=3,
    )
    assert len(refs) == 3
    assert refs[:2] == G[:2]
