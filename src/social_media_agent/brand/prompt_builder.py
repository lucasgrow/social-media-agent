"""Prompt builder — compose text prompt + image refs from brand context + task."""
from pathlib import Path

from social_media_agent.audit.learnings_writer import EMPTY_PLACEHOLDER, NO_DRIFT_PLACEHOLDER


def select_refs(
    grounded: list[Path],
    source: list[Path],
    brand_pages: list[Path],
    limit: int | None = None,
    max_grounded: int = 3,
) -> list[Path]:
    """Assemble the final, de-duplicated, capped image-ref list in priority order.

    Order: grounded subject refs (up to max_grounded) → source layout → brand pages.
    Grounded leads because anchoring the real subject matters more than extra brand
    pages when the engine ref budget (limit, e.g. 5 for gpt-image-2) is tight.
    """
    ordered = list(grounded)[:max_grounded] + list(source) + list(brand_pages)
    seen: set[Path] = set()
    deduped: list[Path] = []
    for p in ordered:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    return deduped[:limit] if limit else deduped


def build_prompt(
    task: str,
    design: dict,
    voice: dict,
    brand_pages: list[Path],
    extra_refs: list[Path],
    learnings_path: Path | None = None,
    learnings_limit: int = 5,
    grounded_refs: list[Path] | None = None,
    ref_limit: int | None = None,
) -> tuple[str, list[Path]]:
    """Compose a prompt for an image generation/edit API call.

    Args:
        task: human-readable description of what to produce
        design: parsed DESIGN.md frontmatter
        voice: parsed VOICE.md frontmatter
        brand_pages: list of brand-kit/pages/*.png paths (always appended to refs)
        extra_refs: additional image refs (layout reference, source image)
        learnings_path: optional path to <profile>/learnings.md (read + injected)
        learnings_limit: cap per-bucket (do_this, avoid) when injecting learnings

    Returns:
        (text_prompt, image_refs_in_order)
    """
    palette = design.get("palette", {})
    fonts = design.get("fonts", {})
    principles = design.get("principles", [])
    anti_refs = design.get("anti_refs", [])

    tone = voice.get("tone", [])
    no_go = voice.get("no_go_words", [])

    sections = []
    sections.append(f"TASK: {task}")
    sections.append("")
    sections.append("BRAND PALETTE (use these exact hex colors):")
    for name, hex_val in palette.items():
        sections.append(f"- {name}: {hex_val}")
    sections.append("")
    sections.append("BRAND TYPOGRAPHY:")
    for role, font in fonts.items():
        sections.append(f"- {role}: {font}")
    if principles:
        sections.append("")
        sections.append("PRINCIPLES:")
        for p in principles:
            sections.append(f"- {p}")
    if anti_refs:
        sections.append("")
        sections.append("AVOID (anti-references):")
        for a in anti_refs:
            sections.append(f"- {a}")

    # Mark rule — stops the model from inventing an emblem/monogram when the brand has no logo
    mark = design.get("mark", {})
    if mark.get("type") == "none":
        sections.append("")
        sections.append(
            "BRAND MARK: NO emblem, NO monogram, NO logo. "
            "The brand has no official mark — never invent letters, oval cartouches, "
            "fleurs-de-lis, or any emblem-like glyph. Use only thin caligraphic "
            "flourishes (✦ ❦ hairline rules) for ornament."
        )

    # Rendering-quality guard — image models glitch human anatomy (the "extra hand" bug).
    # Harmless for purely typographic slides; critical when a person is depicted.
    sections.append("")
    sections.append(
        "RENDERING QUALITY: render correct, natural anatomy. Each person has exactly two arms "
        "and two hands; no extra, duplicated, or floating limbs; no merged or malformed fingers. "
        "Render any text accurately, with correct spelling."
    )

    if tone:
        sections.append("")
        sections.append(f"VOICE TONE: {', '.join(tone)}")
    if no_go:
        sections.append(f"NEVER USE these words: {', '.join(no_go)}")

    # Learnings injection — Phase 4
    if learnings_path is not None and learnings_path.is_file():
        body = learnings_path.read_text()
        do_this = _extract_bulletized_section(body, "Do this")[:learnings_limit]
        avoid = _extract_bulletized_section(body, "Avoid")[:learnings_limit]
        if do_this or avoid:
            sections.append("")
            sections.append("RECENT LEARNINGS for this profile (apply these):")
            for item in do_this:
                sections.append(f"- DO: {item}")
            for item in avoid:
                sections.append(f"- AVOID: {item}")

    # Image refs: grounded subject refs first, then source layout, then brand pages.
    image_refs = select_refs(
        grounded=grounded_refs or [],
        source=extra_refs,
        brand_pages=brand_pages,
        limit=ref_limit,
    )

    return "\n".join(sections), image_refs


def _extract_bulletized_section(body: str, heading_substr: str) -> list[str]:
    """Extract bullet items from a markdown section whose heading contains heading_substr."""
    lines = body.split("\n")
    items: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith("## ") and heading_substr in line:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if (
            in_section
            and line.startswith("- ")
            and EMPTY_PLACEHOLDER not in line
            and NO_DRIFT_PLACEHOLDER not in line
        ):
            items.append(line[2:].strip())
    return items
