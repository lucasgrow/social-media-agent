"""Decisions log — per-post iteration trail (prompts, reactions)."""
from datetime import datetime
from pathlib import Path


def init_log(path: Path, post_slug: str) -> None:
    """Create decisions.md with a header. No-op if file already exists."""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Decisions log — {post_slug}\n\n")


def append_entry(
    path: Path,
    version: str,
    prompt: str,
    note: str = "",
) -> None:
    """Append a versioned entry to the decisions log.

    Auto-initializes the log file with a generic header if missing.
    """
    if not path.exists():
        init_log(path, post_slug=path.parent.name)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    section = [
        f"## {version}",
        f"- timestamp: {timestamp}",
    ]
    if note:
        section.append(f"- note: {note}")
    section.extend([
        "",
        "<details><summary>prompt</summary>",
        "",
        "```",
        prompt,
        "```",
        "</details>",
        "",
    ])
    with path.open("a") as f:
        f.write("\n".join(section) + "\n")
