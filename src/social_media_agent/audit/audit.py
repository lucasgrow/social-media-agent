"""Audit orchestrator — full scan → drift → patterns → learnings write."""
from pathlib import Path

from social_media_agent.audit.decisions_parser import parse_decisions
from social_media_agent.audit.drift_detector import detect_drift
from social_media_agent.audit.learnings_writer import write_learnings
from social_media_agent.audit.pattern_extractor import extract_patterns
from social_media_agent.audit.post_scanner import scan_posts


def run_audit(profile_dir: Path, api_key: str) -> dict:
    """Run full audit on a profile and write learnings.md.

    Returns: {"posts_analyzed": int, "learnings_path": Path, "drifts": list, "patterns": dict}
    """
    posts = scan_posts(profile_dir)

    # Build brand_pages dict for drift detection
    pages_dir = profile_dir / "brand-kit" / "pages"
    brand_pages: dict[str, Path] = {}
    if pages_dir.is_dir():
        for p in pages_dir.iterdir():
            # Normalize "03-paleta.png" → "paleta"
            stem = p.stem
            role = stem.split("-", 1)[-1] if "-" in stem else stem
            brand_pages[role] = p

    # Drift detection per post (against the first final output)
    drifts = []
    for post in posts:
        if not post["final_outputs"]:
            continue
        d = detect_drift(
            api_key=api_key,
            output_image=post["final_outputs"][0],
            brand_pages=brand_pages,
        )
        d["post_slug"] = post["post_dir"].name
        drifts.append(d)

    # Decisions parse per post
    decisions_per_post = []
    for post in posts:
        if post["decisions_path"] is None:
            continue
        iterations = parse_decisions(post["decisions_path"])
        decisions_per_post.append({
            "post_slug": post["post_dir"].name,
            "iterations": iterations,
        })

    # Pattern extraction across all decisions
    patterns = extract_patterns(api_key=api_key, decisions_per_post=decisions_per_post)

    # Write learnings
    learnings_path = write_learnings(
        profile_dir=profile_dir,
        patterns=patterns,
        drifts=drifts,
        posts_analyzed=len(posts),
    )

    return {
        "posts_analyzed": len(posts),
        "learnings_path": learnings_path,
        "drifts": drifts,
        "patterns": patterns,
    }
