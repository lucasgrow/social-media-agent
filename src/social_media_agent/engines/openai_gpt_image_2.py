"""OpenAI gpt-image-2 engine adapter — generate + edit."""
import base64
from pathlib import Path

import requests

API_BASE = "https://api.openai.com/v1"
MODEL = "gpt-image-2-2026-04-21"
MAX_REFS = 5
API_KEY_ENV = "OPENAI_API_KEY"


def generate(
    api_key: str,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "high",
    timeout: int = 300,
) -> bytes:
    """Call OpenAI /v1/images/generations and return PNG bytes."""
    url = f"{API_BASE}/images/generations"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality,
        "output_format": "png",
    }
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"OpenAI API error: {data['error'].get('message', data['error'])}")
    return base64.b64decode(data["data"][0]["b64_json"])


def edit(
    api_key: str,
    prompt: str,
    images: list[Path],
    size: str = "1024x1024",
    quality: str = "high",
    timeout: int = 300,
) -> bytes:
    """Call OpenAI /v1/images/edits with multiple image refs (1-5)."""
    if len(images) < 1:
        raise ValueError("edit() requires at least 1 image")
    if len(images) > MAX_REFS:
        raise ValueError(f"edit() accepts at most {MAX_REFS} images (OpenAI API limit)")

    url = f"{API_BASE}/images/edits"
    headers = {"Authorization": f"Bearer {api_key}"}

    files = []
    for img_path in images:
        mime = "image/png" if str(img_path).lower().endswith(".png") else "image/jpeg"
        files.append(("image[]", (img_path.name, img_path.read_bytes(), mime)))

    data = {
        "model": MODEL,
        "prompt": prompt,
        "n": "1",
        "size": size,
        "quality": quality,
        "output_format": "png",
    }

    response = requests.post(url, headers=headers, files=files, data=data, timeout=timeout)
    response.raise_for_status()
    js = response.json()
    if "error" in js:
        raise RuntimeError(f"OpenAI API error: {js['error'].get('message', js['error'])}")
    return base64.b64decode(js["data"][0]["b64_json"])
