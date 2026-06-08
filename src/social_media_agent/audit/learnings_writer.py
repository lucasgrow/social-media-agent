"""Learnings writer — render learnings.md from extracted patterns + drift list."""
from datetime import date
from pathlib import Path


# Shared with prompt_builder._extract_bulletized_section — the builder filters these
# placeholder lines when reading learnings.md so they don't get injected into prompts.
EMPTY_PLACEHOLDER = "(none)"
NO_DRIFT_PLACEHOLDER = "(no drift detected)"


LEARNINGS_TEMPLATE = """---
last_audit: {today}
posts_analyzed: {posts_analyzed}
---

# Learnings — {profile_name}

## Do this (patterns que funcionaram)
{do_this}

## Avoid (anti-patterns)
{avoid}

## Voice patterns (do legendas)
{voice_patterns}

## Engagement signals (manual feedback)
{engagement_signals}

## Brand drift detected (last audit)
{drifts}
"""


def _bulletize(items: list[str]) -> str:
    if not items:
        return f"- {EMPTY_PLACEHOLDER}"
    return "\n".join(f"- {item}" for item in items)


def _format_drifts(drifts: list[dict]) -> str:
    if not drifts:
        return f"- {NO_DRIFT_PLACEHOLDER}"
    lines = []
    for d in drifts:
        slug = d.get("post_slug", "?")
        flags = []
        if d.get("palette_drift"):
            flags.append("palette_drift")
        if d.get("font_drift"):
            flags.append("font_drift")
        for v in d.get("donts_violations", []):
            flags.append(f"donts: {v}")
        if flags:
            lines.append(f"- {slug}: {', '.join(flags)}")
    return "\n".join(lines) if lines else f"- {NO_DRIFT_PLACEHOLDER}"


def write_learnings(
    profile_dir: Path,
    patterns: dict,
    drifts: list[dict],
    posts_analyzed: int,
) -> Path:
    """Render learnings.md and write to profile_dir/learnings.md.

    Overwrites any existing file (caller should preserve a backup if diff is needed).
    """
    text = LEARNINGS_TEMPLATE.format(
        today=date.today().isoformat(),
        posts_analyzed=posts_analyzed,
        profile_name=profile_dir.name,
        do_this=_bulletize(patterns.get("do_this", [])),
        avoid=_bulletize(patterns.get("avoid", [])),
        voice_patterns=_bulletize(patterns.get("voice_patterns", [])),
        engagement_signals=_bulletize(patterns.get("engagement_signals", [])),
        drifts=_format_drifts(drifts),
    )
    out_path = profile_dir / "learnings.md"
    out_path.write_text(text)
    return out_path
