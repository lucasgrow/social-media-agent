"""Decisions parser — read decisions.md written by Phase 3 decisions_log.append_entry."""
import re
from pathlib import Path


# Matches a versioned section. Captures version, body until next `## ` or EOF.
_SECTION_RE = re.compile(
    r"^## (?P<version>\S+)\n(?P<body>.*?)(?=\n## |\Z)",
    re.DOTALL | re.MULTILINE,
)


def parse_decisions(path: Path) -> list[dict]:
    """Parse a decisions.md and return ordered list of iteration entries.

    Each entry: {version, prompt, note, timestamp}

    Empty list if file missing or has no entries.
    """
    if not path.is_file():
        return []
    text = path.read_text()

    entries = []
    for match in _SECTION_RE.finditer(text):
        version = match.group("version").strip()
        body = match.group("body")
        timestamp = _extract_field(body, "timestamp")
        note = _extract_field(body, "note")
        prompt = _extract_prompt_block(body)
        entries.append({
            "version": version,
            "prompt": prompt,
            "note": note,
            "timestamp": timestamp,
        })
    return entries


def _extract_field(body: str, name: str) -> str:
    """Extract value from a line like `- {name}: {value}`."""
    pattern = rf"^- {re.escape(name)}: (?P<v>.+)$"
    match = re.search(pattern, body, re.MULTILINE)
    return match.group("v").strip() if match else ""


def _extract_prompt_block(body: str) -> str:
    """Extract the prompt from a fenced ``` block inside <details>."""
    match = re.search(r"```\n(?P<p>.*?)\n```", body, re.DOTALL)
    return match.group("p") if match else ""
