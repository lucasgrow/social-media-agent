"""Stage 1 — extract real-world subjects from a brief that need visual grounding."""
from social_media_agent.engines.openai_vision import DEFAULT_MODEL, extract_structured
from social_media_agent.grounding import parse_json_lenient

VALID_KINDS = {"person", "place", "object", "saint", "other"}

PROMPT_TEMPLATE = """You are preparing an image-generation brief. Identify the REAL-WORLD subjects \
in the task below that must look like the actual thing (so the model should be anchored to real \
reference images, not its imagination).

Include only subjects with an established real appearance, e.g.:
- a specific real person (public figure, named individual)
- a specific place or building (a named church, square, city landmark)
- a saint or religious figure with established iconography
- a specific real product or branded object

EXCLUDE generic/abstract things the model can invent freely (generic people, abstract shapes,
typography, moods, colors, generic backgrounds).

Return a JSON array (and nothing else). Each item:
{{"name": "...", "kind": "person|place|object|saint|other", "search_query": "<good web image search query>", "why": "<one short line>"}}

If nothing needs grounding, return exactly: []

TASK:
{task}
"""


def extract_subjects(task: str, api_key: str, model: str = DEFAULT_MODEL) -> list[dict]:
    """Return the list of real-world subjects in `task` that need grounding ([] if none).

    Each subject dict: {name, kind, search_query, why}. Malformed/unknown kinds are
    normalized to "other"; a non-list LLM response yields [].
    """
    prompt = PROMPT_TEMPLATE.format(task=task)
    response = extract_structured(api_key=api_key, prompt=prompt, model=model)
    parsed = parse_json_lenient(response)
    if not isinstance(parsed, list):
        return []

    subjects = []
    for item in parsed:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        kind = str(item.get("kind", "other")).lower()
        subjects.append(
            {
                "name": str(item["name"]).strip(),
                "kind": kind if kind in VALID_KINDS else "other",
                "search_query": str(item.get("search_query") or item["name"]).strip(),
                "why": str(item.get("why", "")).strip(),
            }
        )
    return subjects
