"""Post scanner — enumerate all posts in a profile that have final outputs."""
from pathlib import Path


def scan_posts(profile_dir: Path) -> list[dict]:
    """Return list of all post entries that have at least one file in outputs/final/.

    Each entry: {
        "post_dir": Path,
        "final_outputs": list[Path],
        "decisions_path": Path | None,
    }

    Sorted by post_dir path (chronological by YYYY-MM/NN-slug ordering).
    """
    posts_root = profile_dir / "posts"
    if not posts_root.is_dir():
        return []

    entries = []
    for month_dir in sorted(posts_root.iterdir()):
        if not month_dir.is_dir():
            continue
        for post_dir in sorted(month_dir.iterdir()):
            if not post_dir.is_dir():
                continue
            final_dir = post_dir / "outputs" / "final"
            if not final_dir.is_dir():
                continue
            final_outputs = sorted(p for p in final_dir.iterdir() if p.is_file())
            if not final_outputs:
                continue
            decisions = post_dir / "decisions.md"
            entries.append({
                "post_dir": post_dir,
                "final_outputs": final_outputs,
                "decisions_path": decisions if decisions.is_file() else None,
            })
    return entries
