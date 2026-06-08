"""Pattern extractor — LLM synth from per-post decisions.md."""
import json

from social_media_agent.engines.openai_vision import DEFAULT_MODEL, extract_structured


PROMPT_TEMPLATE = """You are a content-strategy analyst for the social-media-agent system.

Below are the iteration histories (decisions.md) from {n_posts} posts of a single profile.
Each post has versioned iterations (v1, v2, ...) with the prompt that produced it and an optional note about user reaction.

Extract patterns across all posts:
- do_this: design/voice patterns that produced approved-on-v1 results OR were repeatedly successful
- avoid: patterns that required 3+ iterations OR had "refazer" / negative notes
- voice_patterns: recurring tone/copy patterns observed in prompts that worked
- engagement_signals: explicit engagement annotations (manual user feedback like "esse funcionou", "flop")

POSTS DATA:
{decisions_block}

Return ONLY a JSON object with this exact shape:
{{
  "do_this": [strings],
  "avoid": [strings],
  "voice_patterns": [strings],
  "engagement_signals": [strings]
}}

No prose. JSON only."""


def extract_patterns(api_key: str, decisions_per_post: list[dict], model: str = DEFAULT_MODEL) -> dict:
    """LLM-synth patterns across all posts' decisions.

    Args:
        api_key: OPENAI_API_KEY
        decisions_per_post: list of {"post_slug": str, "iterations": list[dict]}
        model: text LLM model

    Returns:
        {"do_this": [...], "avoid": [...], "voice_patterns": [...], "engagement_signals": [...]}
        On parse failure, defaults + "raw" key.
    """
    n_posts = len(decisions_per_post)
    blocks = []
    for post in decisions_per_post:
        blocks.append(f"## {post['post_slug']}")
        for it in post.get("iterations", []):
            note = it.get("note", "")
            note_str = f" — note: {note}" if note else ""
            blocks.append(f"- {it['version']}{note_str}")
            blocks.append(f"  prompt: {it.get('prompt', '')[:500]}")
        blocks.append("")
    decisions_block = "\n".join(blocks) if blocks else "(no posts yet)"

    prompt = PROMPT_TEMPLATE.format(n_posts=n_posts, decisions_block=decisions_block)

    response_text = extract_structured(api_key=api_key, prompt=prompt, model=model)

    try:
        parsed = json.loads(response_text)
        return {
            "do_this": list(parsed.get("do_this", [])),
            "avoid": list(parsed.get("avoid", [])),
            "voice_patterns": list(parsed.get("voice_patterns", [])),
            "engagement_signals": list(parsed.get("engagement_signals", [])),
        }
    except (json.JSONDecodeError, TypeError, ValueError):
        return {
            "do_this": [],
            "avoid": [],
            "voice_patterns": [],
            "engagement_signals": [],
            "raw": response_text,
        }
