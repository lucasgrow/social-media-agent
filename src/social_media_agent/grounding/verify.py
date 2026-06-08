"""Stage 3 — verify a candidate reference image actually depicts the subject."""
from pathlib import Path

from social_media_agent.engines.openai_vision import DEFAULT_MODEL, analyze_image
from social_media_agent.grounding import parse_json_lenient

PROMPT_TEMPLATE = """Does this image actually depict the following subject?

Subject: {name}
Kind: {kind}
{why}

Judge whether the image genuinely shows THIS subject (right person/place/figure/object),
not merely something visually similar or thematically related.

Return JSON only:
{{"match": true|false, "score": <0.0-1.0 confidence it is the subject>, "reason": "<one short line>"}}
"""


def verify_ref(
    subject: dict,
    image_path: Path,
    api_key: str,
    model: str = DEFAULT_MODEL,
    min_score: float = 0.6,
) -> dict:
    """Vision-check `image_path` against `subject`.

    Returns {match: bool, score: float, reason: str}. `match` is gated by both the
    model's boolean and `min_score`, so a low-confidence true is rejected. On a
    parse/API hiccup returns a non-matching verdict with the raw text.
    """
    why = f"Context: {subject['why']}" if subject.get("why") else ""
    prompt = PROMPT_TEMPLATE.format(
        name=subject.get("name", ""), kind=subject.get("kind", "other"), why=why
    )
    response = analyze_image(api_key=api_key, prompt=prompt, image_path=image_path, model=model)
    parsed = parse_json_lenient(response)
    if not isinstance(parsed, dict):
        return {"match": False, "score": 0.0, "reason": "unparseable verdict", "raw": response}

    try:
        score = float(parsed.get("score", 0.0))
    except (TypeError, ValueError):
        score = 0.0
    match = bool(parsed.get("match", False)) and score >= min_score
    return {"match": match, "score": score, "reason": str(parsed.get("reason", "")).strip()}
