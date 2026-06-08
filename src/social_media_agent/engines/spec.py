"""Per-engine, per-format generation specs.

gpt-image-2 sizes by pixel string (e.g. "1024x1280"); Gemini sizes by aspectRatio +
imageSize. resolve_gen_kwargs() returns the right keyword args for an engine+format so
craft.py stays engine-agnostic.
"""
from social_media_agent.engines import gemini_image, get_engine

# OpenAI gpt-image-2 pixel sizes (canonical source — materialize re-exports this).
FORMAT_TO_SIZE = {
    "feed_1x1": "1024x1024",
    "feed_4x5": "1024x1280",
    "carousel_4x5": "1024x1280",
    "story_9x16_still": "1024x1536",
    "reel_9x16": "1024x1536",
    "story_video_9x16": "1024x1536",
}

# Gemini aspect ratios.
FORMAT_TO_ASPECT = {
    "feed_1x1": "1:1",
    "feed_4x5": "4:5",
    "carousel_4x5": "4:5",
    "story_9x16_still": "9:16",
    "reel_9x16": "9:16",
    "story_video_9x16": "9:16",
}

DEFAULT_SIZE = "1024x1280"
DEFAULT_ASPECT = "4:5"
GEMINI_IMAGE_SIZE = "2K"


def resolve_gen_kwargs(engine_name: str, format_: str) -> dict:
    """Keyword args for the engine's generate()/edit() given a post format."""
    engine = get_engine(engine_name)
    if engine is gemini_image:
        return {
            "aspect_ratio": FORMAT_TO_ASPECT.get(format_, DEFAULT_ASPECT),
            "image_size": GEMINI_IMAGE_SIZE,
        }
    return {"size": FORMAT_TO_SIZE.get(format_, DEFAULT_SIZE), "quality": "high"}
