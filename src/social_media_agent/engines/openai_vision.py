"""OpenAI vision + text-extraction adapter (chat-completions API).

Two entry points:
- analyze_image: multimodal call with text + base64 image (for drift detection)
- extract_structured: text-only call (for pattern extraction from decisions.md)

Both use the same /v1/chat/completions endpoint with different message content shape.
"""
import base64
from pathlib import Path

import requests

API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-5"


def analyze_image(
    api_key: str,
    prompt: str,
    image_path: Path,
    model: str = DEFAULT_MODEL,
    timeout: int = 120,
) -> str:
    """Send a multimodal (text + image) message to OpenAI chat-completions.

    Returns the assistant's text response.
    Raises RuntimeError if API returns error.
    """
    image_bytes = image_path.read_bytes()
    image_b64 = base64.b64encode(image_bytes).decode()
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
                ],
            }
        ],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"OpenAI vision error: {data['error'].get('message', data['error'])}")
    return data["choices"][0]["message"]["content"]


def extract_structured(
    api_key: str,
    prompt: str,
    model: str = DEFAULT_MODEL,
    timeout: int = 120,
) -> str:
    """Send a text-only message to OpenAI chat-completions and return the response text.

    Caller is responsible for parsing the response (e.g. as JSON).
    """
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"OpenAI extract error: {data['error'].get('message', data['error'])}")
    return data["choices"][0]["message"]["content"]
