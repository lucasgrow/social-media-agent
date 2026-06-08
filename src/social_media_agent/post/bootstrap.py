"""Post folder bootstrap — create posts/YYYY-MM/NN-slug/ + populate source/ + brief.md."""
import json
import re
import shutil
from datetime import date
from pathlib import Path


BRIEF_TEMPLATE = """---
profile: {profile}
slug: {slug}
format: {format_}
engine: {engine}
context: utility
created: {today}
source_url: {source_url}
---

# Brief — {slug}

(Fill in: what should the post say? What's the hero text? Tone?)

## Source context (auto-extracted)

{source_summary}

## Acceptance

- Format: {format_}
- Engine: {engine}
- (Add specific design or copy requirements here.)
"""


def _next_post_number(month_dir: Path) -> int:
    if not month_dir.is_dir():
        return 1
    existing_numbers = []
    for entry in month_dir.iterdir():
        if entry.is_dir():
            match = re.match(r"^(\d+)-", entry.name)
            if match:
                existing_numbers.append(int(match.group(1)))
    return (max(existing_numbers) + 1) if existing_numbers else 1


def bootstrap_post(
    profile_dir: Path,
    slug: str,
    year_month: str,
    format_: str,
    engine: str,
    source_url: str | None,
    source_files: list[Path],
    source_meta: dict,
) -> dict:
    """Create a new post folder under profile_dir/posts/YYYY-MM/.

    Returns: {"post_dir": Path, "number": int}
    """
    month_dir = profile_dir / "posts" / year_month
    number = _next_post_number(month_dir)
    post_dir = month_dir / f"{number:02d}-{slug}"
    post_dir.mkdir(parents=True, exist_ok=False)

    source_dir = post_dir / "source"
    source_dir.mkdir()

    if source_url:
        (source_dir / "original-link.txt").write_text(source_url + "\n")
    (source_dir / "meta.json").write_text(json.dumps(source_meta, indent=2, ensure_ascii=False))

    for f in source_files:
        if f.is_file():
            shutil.copy2(f, source_dir / f.name)

    source_summary = "(no source ingested)" if not source_files else "\n".join(
        f"- {f.name}" for f in source_files
    )

    brief = BRIEF_TEMPLATE.format(
        profile=profile_dir.name,
        slug=slug,
        format_=format_,
        engine=engine,
        today=date.today().isoformat(),
        source_url=source_url or "(none)",
        source_summary=source_summary,
    )
    (post_dir / "brief.md").write_text(brief)

    return {"post_dir": post_dir, "number": number}
