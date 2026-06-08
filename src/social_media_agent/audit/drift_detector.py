"""Drift detector — Vision compare output PNG vs brand-kit/pages."""
import json
from pathlib import Path

from social_media_agent.engines.openai_vision import DEFAULT_MODEL, analyze_image


PROMPT_TEMPLATE = """You are a brand-compliance auditor for the social-media-agent system.

Given THIS image (the actual finalized post), assess drift vs the brand identity:
- palette_drift: True if any prominent color is NOT in the brand palette
- font_drift: True if any visible text uses a font NOT in the brand typography
- donts_violations: list of specific brand anti-patterns found (e.g., "uses cartoon style", "has emoji on slide")

{brand_context}

Return ONLY a JSON object with this exact shape:
{{
  "palette_drift": bool,
  "font_drift": bool,
  "donts_violations": [strings]
}}

No prose. JSON only."""


def detect_drift(
    api_key: str,
    output_image: Path,
    brand_pages: dict[str, Path],
    model: str = DEFAULT_MODEL,
) -> dict:
    """Compare output_image against brand pages and return drift flags.

    Args:
        api_key: OPENAI_API_KEY
        output_image: the post PNG to audit
        brand_pages: dict mapping role (paleta, tipografia, donts) to Path of brand page
        model: vision model

    Returns:
        {"palette_drift": bool, "font_drift": bool, "donts_violations": list[str]}
        On parse failure, returns same shape with defaults + "raw" key with the LLM response.

    NOTE: palette_drift is heuristic — the model has no actual palette reference,
    only the output image + a textual hint about where brand pages live. It catches
    gross violations (wrong color family) but misses subtle hex mismatches.
    Phase 5 may extend analyze_image to accept multiple images and send the
    actual palette page alongside the output for proper visual comparison.
    """
    brand_context_lines = []
    if brand_pages:
        brand_context_lines.append("Brand reference pages (described, since you only see the output):")
        for role, _ in brand_pages.items():
            brand_context_lines.append(f"- {role}: see brand-kit/pages/{role}.png in the project")
    brand_context = "\n".join(brand_context_lines) if brand_context_lines else ""

    prompt = PROMPT_TEMPLATE.format(brand_context=brand_context)

    response_text = analyze_image(
        api_key=api_key,
        prompt=prompt,
        image_path=output_image,
        model=model,
    )

    try:
        parsed = json.loads(response_text)
        return {
            "palette_drift": bool(parsed.get("palette_drift", False)),
            "font_drift": bool(parsed.get("font_drift", False)),
            "donts_violations": list(parsed.get("donts_violations", [])),
        }
    except (json.JSONDecodeError, TypeError, ValueError):
        return {
            "palette_drift": False,
            "font_drift": False,
            "donts_violations": [],
            "raw": response_text,
        }
