"""
Image preview renderer for AndroidTUI.
Generates 24-bit truecolor half-block ANSI representations of images
directly inside the terminal preview pane, inspired by pikpaktui's image_render.rs.
"""
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from rich.text import Text
from rich.style import Style
from rich.color import Color

try:
    from PIL import Image, ImageDraw
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


CACHE_DIR = Path.home() / ".cache" / "android_tui"


def get_cache_thumb_path() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / "current_preview.thumb"


def render_image_halfblock(
    img: "Image.Image",
    max_width: int = 34,
    max_height: int = 16,
) -> Text:
    """
    Renders a PIL image as a Rich Text object using Unicode upper half-block '▀' (\\u2580).
    Each terminal cell represents two pixels vertically (top = fg, bottom = bg).
    """
    orig_w, orig_h = img.size
    if orig_w == 0 or orig_h == 0 or max_width <= 0 or max_height <= 0:
        return Text("[Immagine vuota o non valida]", style="dim")

    # Terminal cells are roughly 2x taller than wide.
    # Therefore, aspect ratio in cells is (orig_w / orig_h) * 2.0
    orig_aspect = orig_w / orig_h
    cell_aspect = orig_aspect * 2.0

    target_w = max_width
    target_h = int(target_w / cell_aspect)

    if target_h > max_height:
        target_h = max_height
        target_w = max(1, int(target_h * cell_aspect))

    # Resize image to target_w x (target_h * 2) pixels
    pixel_w = max(1, target_w)
    pixel_h = max(2, target_h * 2)

    img_rgb = img.convert("RGB").resize((pixel_w, pixel_h), Image.Resampling.LANCZOS)
    pixels = img_rgb.load()

    rich_text = Text()

    for y in range(target_h):
        y_top = y * 2
        y_bottom = min(y * 2 + 1, pixel_h - 1)

        for x in range(pixel_w):
            r1, g1, b1 = pixels[x, y_top]
            r2, g2, b2 = pixels[x, y_bottom]

            rich_text.append(
                "▀",
                style=Style(
                    color=Color.from_rgb(r1, g1, b1),
                    bgcolor=Color.from_rgb(r2, g2, b2),
                ),
            )
        rich_text.append("\n")

    return rich_text


def generate_demo_image(name: str) -> "Image.Image":
    """Generates a demo graphic thumbnail with gradients for simulation mode."""
    img = Image.new("RGB", (320, 240), color=(26, 27, 38))
    draw = ImageDraw.Draw(img)
    # Sunset gradient / landscape
    for y in range(160):
        r = int(122 + y * 0.8)
        g = int(60 + y * 0.5)
        b = int(180 - y * 0.7)
        draw.line([(0, y), (320, y)], fill=(min(255, r), min(255, g), max(0, b)))
    # Mountains
    draw.polygon([(40, 160), (120, 80), (200, 160)], fill=(45, 50, 75))
    draw.polygon([(140, 160), (220, 95), (300, 160)], fill=(35, 40, 60))
    # Sun
    draw.ellipse([(210, 40), (260, 90)], fill=(255, 200, 100))
    # Foreground ground
    draw.rectangle([(0, 160), (320, 240)], fill=(20, 25, 40))
    return img


def load_image_thumbnail(
    remote_path: str,
    adb_manager,
    max_width: int = 34,
    max_height: int = 15,
) -> Tuple[Optional[Text], Optional[str]]:
    """
    Downloads or retrieves image and renders a 24-bit half-block thumbnail.
    Returns (Rich Text, dimensions_string).
    """
    if not HAS_PILLOW:
        return None, "Libreria Pillow non installata"

    if adb_manager.demo_mode:
        img = generate_demo_image(remote_path)
        return render_image_halfblock(img, max_width, max_height), "320x240 px (Demo)"

    cache_file = get_cache_thumb_path()
    if cache_file.exists():
        try:
            cache_file.unlink()
        except Exception:
            pass

    # Pull file to temp cache
    success, _ = adb_manager.pull_file(remote_path, str(cache_file.parent))
    target = cache_file.parent / Path(remote_path).name

    if not target.exists():
        return None, "Impossibile scaricare thumbnail"

    try:
        with Image.open(target) as img:
            dim_str = f"{img.width}x{img.height} px"
            text_render = render_image_halfblock(img, max_width, max_height)
        # Clean up pulled temp file
        try:
            target.unlink()
        except Exception:
            pass
        return text_render, dim_str
    except Exception as e:
        return None, f"Errore decodifica: {e}"
