"""Render text-dominant slides to PNG via headless Chromium (Playwright).

A slide that is mostly TEXT (a legend, body copy, info/hours, a table) is a typography
and layout problem, NOT an image-generation problem: diffusion models (gpt-image) render
long text unreliably — wrong glyphs, misspellings, fonts they cannot hold. So text slides
are rendered here, deterministically, with real fonts (Helvetica display + Garamond body),
crisp and correct. Image-dominant slides go to the image engine instead.

`render_html` is the engine (HTML string → PNG). `text_slide_html` builds the OpenSaints/
brand-styled HTML for a text slide from the profile DESIGN palette/fonts.
"""
import html as _html
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


def render_html(
    html_str: str,
    out_path: Path,
    width: int = 1024,
    height: int = 1280,
    scale: int = 2,
) -> Path:
    """Render `html_str` to a PNG of exactly width×height (rendered at `scale`× then downscaled).

    Raises:
        RuntimeError if Chromium isn't installed (run: python -m playwright install chromium).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".hi.png")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=scale,
            )
            page.set_content(html_str, wait_until="networkidle")
            page.screenshot(path=str(tmp), clip={"x": 0, "y": 0, "width": width, "height": height})
            browser.close()
    except Exception as exc:  # noqa: BLE001 — surface a clear, actionable error
        msg = str(exc)
        if "Executable doesn't exist" in msg or "playwright install" in msg:
            raise RuntimeError(
                "Chromium not installed for Playwright. Run: "
                ".venv/bin/python -m playwright install chromium"
            ) from exc
        raise RuntimeError(f"HTML render failed: {exc}") from exc

    # Downscale the 2× capture to the exact target for crisp anti-aliased text.
    with Image.open(tmp) as img:
        img = img.convert("RGB").resize((width, height), Image.LANCZOS)
        img.save(out_path)
    tmp.unlink(missing_ok=True)
    return out_path


def _font_stack(fonts: dict, role: str, fallback: str) -> str:
    name = fonts.get(role)
    return f'"{name}", {fallback}' if name else fallback


def text_slide_html(
    design: dict,
    title: str,
    paragraphs: list[str],
    source: str | None = None,
    kicker: str | None = None,
    width: int = 1024,
    height: int = 1280,
) -> str:
    """Build a text-dominant slide in the light NASA register from the profile DESIGN meta.

    Design standard layered here: /readable (type scale, measure, leading) + /nasa-style
    (Helvetica display, Garamond reading body, bold red accent, strict flush-left grid) +
    /impeccable shared laws (OKLCH tinted neutrals — never pure #000/#fff; ≥1.25 scale ratio
    between kicker → title → body; rhythmic, non-uniform spacing; an editorial drop-cap detail;
    no side-stripe borders, no gradient text). Three-tier hierarchy: red kicker, black title,
    Garamond body; a red hairline + source label pinned to the foot.
    """
    palette = design.get("palette", {})
    fonts = design.get("fonts", {})
    # Light register for text slides: paper background (NOT the profile's dark image field),
    # OKLCH-tinted neutrals so nothing is pure black/white, bold NASA red as the one accent.
    bg = palette.get("paper") or palette.get("background", "oklch(0.972 0.008 70)")
    ink = palette.get("ink", "oklch(0.21 0.013 40)")
    accent = palette.get("accent", "#C8102E")
    display = _font_stack(fonts, "display", '"Helvetica Neue", Helvetica, Arial, sans-serif')
    serif = _font_stack(fonts, "serif", '"EB Garamond", Garamond, Georgia, serif')

    bad = next((p for p in paragraphs if not isinstance(p, str)), None)
    if bad is not None:
        raise ValueError(
            f"text_slide_html: every paragraph must be a string, got {type(bad).__name__}. "
            "A YAML list item containing ': ' parses as a mapping — quote it in the brief."
        )
    body = "\n".join(f"<p>{_html.escape(p)}</p>" for p in paragraphs)
    kicker_html = f'<div class="kicker">{_html.escape(kicker)}</div>' if kicker else '<div class="bar"></div>'
    src_html = f'<div class="src">{_html.escape(source)}</div>' if source else ""
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital@0;1&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: {width}px; height: {height}px; }}
  body {{
    background: {bg}; color: {ink};
    padding: 96px 84px 152px;
    display: flex; flex-direction: column; justify-content: center;
    position: relative;
    -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
  }}
  /* hierarchy: red kicker (or marker bar) → black Helvetica title → Garamond body.
     spacing is deliberately uneven to create rhythm, not a uniform stack. */
  .kicker {{
    font-family: {display}; font-weight: 700;
    font-size: 23px; text-transform: uppercase; letter-spacing: 0.14em;
    color: {accent}; margin-bottom: 26px;
  }}
  .bar {{ width: 120px; height: 10px; background: {accent}; margin-bottom: 40px; }}
  .title {{
    font-family: {display};
    font-weight: 800; text-transform: uppercase;
    font-size: 64px; line-height: 1.04; letter-spacing: -0.01em;
    color: {ink};
    margin-bottom: 52px;
  }}
  .body p {{
    font-family: {serif};
    font-size: 43px; line-height: 1.52;
    color: {ink};
    margin-bottom: 30px;
  }}
  .body p:last-child {{ margin-bottom: 0; }}
  /* editorial detail: a red Garamond drop-cap on the opening paragraph */
  .body p:first-of-type::first-letter {{
    font-family: {serif}; font-weight: 600;
    color: {accent};
    font-size: 1.9em; line-height: 0.9;
    float: left; margin: 8px 14px 0 0;
  }}
  footer {{ position: absolute; left: 84px; right: 84px; bottom: 76px; }}
  .rule {{ height: 3px; background: {accent}; width: 100%; margin-bottom: 20px; }}
  .src {{
    font-family: {display}; font-weight: 700;
    font-size: 22px; text-transform: uppercase; letter-spacing: 0.08em;
    color: {accent};
  }}
</style></head>
<body>
  <div class="main">
    {kicker_html}
    <div class="title">{_html.escape(title)}</div>
    <div class="body">
      {body}
    </div>
  </div>
  <footer>
    <div class="rule"></div>
    {src_html}
  </footer>
</body></html>"""
