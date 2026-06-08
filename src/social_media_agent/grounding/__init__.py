"""Grounded image generation — anchor real-world subjects (people, places, saints,
buildings, products) to real reference images before generation.

Ports stages 1-3 of the opennanobanana flow into the package:
    1. extract  — find real-world subjects in the brief that need grounding
    2. search   — optional Serper image search for candidate refs
    3. verify   — vision check that a candidate ref actually depicts the subject
Stage 4 (generation) already exists via engines.*.edit(), which consumes the
validated refs collected here. The conversational layer (SKILL.md Workflow G)
decides *how* refs are acquired (ask user → web search → Serper).
"""
import json


def parse_json_lenient(text: str):
    """json.loads tolerant of ```json fences and surrounding prose. None on failure."""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # drop opening fence (``` or ```json) and trailing fence
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
        if cleaned.endswith("```"):
            cleaned = cleaned[: -3]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, TypeError, ValueError):
        # last resort: grab the outermost [...] or {...}
        for open_c, close_c in (("[", "]"), ("{", "}")):
            i, j = cleaned.find(open_c), cleaned.rfind(close_c)
            if 0 <= i < j:
                try:
                    return json.loads(cleaned[i : j + 1])
                except (json.JSONDecodeError, ValueError):
                    pass
        return None
