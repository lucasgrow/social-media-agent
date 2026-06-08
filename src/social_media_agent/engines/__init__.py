"""Image-generation engine registry.

Each engine module exposes the same surface so they are swappable from craft.py:
    generate(api_key, prompt, ...) -> bytes
    edit(api_key, prompt, images: list[Path], ...) -> bytes
    MAX_REFS: int   # max reference images edit() accepts

A profile picks its engine via DESIGN.md `default_engine`. get_engine() resolves
that name (or a short alias) to the module.
"""
from types import ModuleType

from social_media_agent.engines import gemini_image, openai_gpt_image_2

# Canonical name (== module name) → module. Short aliases map onto the same modules.
_ENGINES: dict[str, ModuleType] = {
    "openai_gpt_image_2": openai_gpt_image_2,
    "gemini_image": gemini_image,
}

_ALIASES: dict[str, str] = {
    "openai": "openai_gpt_image_2",
    "gpt-image-2": "openai_gpt_image_2",
    "gemini": "gemini_image",
    "gemini-3-pro-image-preview": "gemini_image",
    "nano-banana": "gemini_image",
}


def available_engines() -> list[str]:
    """Canonical engine names that get_engine() accepts."""
    return sorted(_ENGINES)


def get_engine(name: str) -> ModuleType:
    """Resolve an engine name (canonical or alias) to its module.

    Raises ValueError on an unknown name, listing the valid options.
    """
    key = _ALIASES.get(name, name)
    engine = _ENGINES.get(key)
    if engine is None:
        raise ValueError(
            f"Unknown engine {name!r}. Available: {', '.join(available_engines())} "
            f"(aliases: {', '.join(sorted(_ALIASES))})"
        )
    return engine
