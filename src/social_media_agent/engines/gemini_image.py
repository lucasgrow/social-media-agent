"""Gemini gemini-3-pro-image-preview engine adapter — generate + edit.

Mirrors the openai_gpt_image_2 adapter (generate/edit) so engines are swappable
via engines.get_engine(). Gemini accepts up to 14 reference images (5 high-fidelity
recommended) vs gpt-image-2's hard limit of 5 — useful for grounded generation where
brand pages + grounded subject refs + source layout would otherwise overflow.

REST API: POST .../models/<model>:generateContent with x-goog-api-key header.
Image bytes come back as candidates[].content.parts[].inlineData.data (base64).
"""
import base64
from pathlib import Path

import requests

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
MODEL = "gemini-3-pro-image-preview"
MAX_REFS = 14
API_KEY_ENV = "GEMINI_API_KEY"


def _mime_for(path: Path) -> str:
    return "image/png" if path.suffix.lower() == ".png" else "image/jpeg"


def _extract_png(data: dict) -> bytes:
    """Pull the first inline image out of a generateContent response.

    Raises RuntimeError on API error or when the response carries no image
    (safety filters drop the image silently — surface that instead of KeyError).
    """
    if "error" in data:
        err = data["error"]
        raise RuntimeError(f"Gemini API error: {err.get('message', err)}")

    candidates = data.get("candidates", [])
    for cand in candidates:
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])

    # No image — usually a safety block or text-only refusal.
    block = ""
    if candidates:
        block = candidates[0].get("finishReason", "")
    raise RuntimeError(
        f"Gemini returned no image (finishReason={block!r}). "
        "Prompt may have been blocked by safety filters — rephrase and retry."
    )


def generate(
    api_key: str,
    prompt: str,
    aspect_ratio: str = "1:1",
    image_size: str = "2K",
    timeout: int = 300,
) -> bytes:
    """Call Gemini generateContent (text-only) and return image bytes."""
    url = f"{API_BASE}/models/{MODEL}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio, "imageSize": image_size},
        },
    }
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return _extract_png(response.json())


def edit(
    api_key: str,
    prompt: str,
    images: list[Path],
    aspect_ratio: str = "1:1",
    image_size: str = "2K",
    timeout: int = 300,
) -> bytes:
    """Call Gemini generateContent with 1-14 reference images and return image bytes."""
    if len(images) < 1:
        raise ValueError("edit() requires at least 1 image")
    if len(images) > MAX_REFS:
        raise ValueError(f"edit() accepts at most {MAX_REFS} images (Gemini API limit)")

    parts: list[dict] = [{"text": prompt}]
    for img_path in images:
        b64 = base64.b64encode(img_path.read_bytes()).decode()
        parts.append({"inline_data": {"mime_type": _mime_for(img_path), "data": b64}})

    url = f"{API_BASE}/models/{MODEL}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio, "imageSize": image_size},
        },
    }
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return _extract_png(response.json())
