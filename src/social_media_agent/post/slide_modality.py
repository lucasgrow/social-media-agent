"""Deterministic per-slide rendering modality — html vs image. Not a judgement call.

HTML is the right tool ONLY when a slide follows a clear, defined template STANDARD —
something with a known, repeatable layout we can render with real fonts:

    legend / quote / info / hours / table / prose   -> "html"

Everything else — art-directed or expressive compositions (display type bleeding off the
edges, integrated imagery, color fields, a cover) — is NOT a generic-template job. A plain
HTML template cannot honour that design; it belongs to the image engine, which adapts the
reference slide. So:

    no recognised template standard  ->  "image"   (default; adapts the reference)

Why a rule and not a guess: "text-heavy → html" is too crude — the most text-heavy slide
can also be the most art-directed (a typographic cover). The deciding question is "is there
a clear template standard to follow?", never "how much text is there?". An explicit
``render:`` on the slide always wins.
"""

HTML = "html"
IMAGE = "image"

# Slide kinds we have a real, defined HTML template standard for.
_TEMPLATED_HTML_KINDS = {"legend", "quote", "info", "hours", "table", "prose", "body", "text"}


def classify(slide: dict) -> str:
    """Return 'html' or 'image' for a slide dict.

    Precedence:
      1. explicit ``slide['render']`` ('html'|'image')
      2. ``kind`` matches a templated HTML standard → html
      3. otherwise → image (no clear standard → not html; adapt the reference)
    """
    explicit = str(slide.get("render", "")).strip().lower()
    if explicit in (HTML, IMAGE):
        return explicit

    kind = str(slide.get("kind", "")).strip().lower()
    if kind in _TEMPLATED_HTML_KINDS:
        return HTML

    return IMAGE


def is_text_dominant(slide: dict) -> bool:
    return classify(slide) == HTML
