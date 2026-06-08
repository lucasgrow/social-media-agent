"""Image renderer — save bytes + composite preview grid."""
from pathlib import Path

from PIL import Image


def save(data: bytes, path: Path) -> None:
    """Write bytes to path, creating parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def preview_grid(slide_paths: list[Path], cols: int = 3, thumb_div: int = 3) -> Image.Image:
    """Composite slide PNGs into a single preview grid image."""
    if not slide_paths:
        raise ValueError("preview_grid requires at least 1 slide")

    sample = Image.open(slide_paths[0])
    tw, th = sample.width // thumb_div, sample.height // thumb_div
    rows = (len(slide_paths) + cols - 1) // cols
    padding = 8
    canvas_w = tw * cols + padding * 2
    canvas_h = th * rows + padding * 2
    canvas = Image.new("RGB", (canvas_w, canvas_h), (240, 240, 240))
    for i, p in enumerate(slide_paths):
        im = Image.open(p).resize((tw, th))
        r, c = i // cols, i % cols
        canvas.paste(im, (c * tw + padding, r * th + padding))
    return canvas
