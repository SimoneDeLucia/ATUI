"""
Image and Video preview renderer for AndroidTUI.
Generates 24-bit truecolor half-block ANSI representations of images and video thumbnails
directly inside the terminal preview pane, inspired by pikpaktui's image_render.rs.
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict
from rich.text import Text
from rich.style import Style
from rich.color import Color

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

try:
    from PIL import Image, ImageDraw
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


CACHE_DIR = Path.home() / ".cache" / "android_tui"
_MEDIA_CACHE: Dict[str, Tuple[Text, str]] = {}


def get_cache_thumb_path(suffix: str = ".thumb") -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"current_preview{suffix}"


def clear_preview_cache() -> None:
    """Deletes all files and directories inside the preview cache directory,
    and resets the in-memory thumbnail cache.
    """
    global _MEDIA_CACHE
    _MEDIA_CACHE.clear()

    try:
        if CACHE_DIR.exists():
            for item in CACHE_DIR.iterdir():
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                except Exception:
                    pass
    except Exception:
        pass


def render_image_halfblock(
    img: "Image.Image",
    max_width: int = 46,
    max_height: int = 20,
) -> Text:
    """
    Renders a PIL image as a Rich Text object using Unicode upper half-block '▀' (\\u2580).
    Each terminal cell represents two pixels vertically (top = fg, bottom = bg).
    High resolution is achieved with LANCZOS resampling.
    """
    orig_w, orig_h = img.size
    if orig_w == 0 or orig_h == 0 or max_width <= 0 or max_height <= 0:
        return Text("[Immagine vuota o non valida]", style="dim")

    # Terminal cells are roughly 2.0x taller than wide.
    orig_aspect = orig_w / orig_h
    cell_aspect = orig_aspect * 2.0

    target_w = max_width
    target_h = int(target_w / cell_aspect)

    if target_h > max_height:
        target_h = max_height
        target_w = max(1, int(target_h * cell_aspect))

    # Resize image to target_w x (target_h * 2) pixels for high resolution half-blocks
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
    img = Image.new("RGB", (480, 320), color=(26, 27, 38))
    draw = ImageDraw.Draw(img)
    for y in range(200):
        r = int(122 + y * 0.6)
        g = int(60 + y * 0.4)
        b = int(180 - y * 0.5)
        draw.line([(0, y), (480, y)], fill=(min(255, r), min(255, g), max(0, b)))
    draw.polygon([(60, 200), (180, 100), (300, 200)], fill=(45, 50, 75))
    draw.polygon([(200, 200), (320, 120), (440, 200)], fill=(35, 40, 60))
    draw.ellipse([(310, 50), (380, 120)], fill=(255, 200, 100))
    draw.rectangle([(0, 200), (480, 320)], fill=(20, 25, 40))
    return img


def generate_video_demo(name: str) -> "Image.Image":
    """Generates a demo video thumbnail with a film slate and play watermark."""
    img = Image.new("RGB", (480, 270), color=(15, 20, 32))
    draw = ImageDraw.Draw(img)
    # Background gradient
    for y in range(270):
        draw.line([(0, y), (480, y)], fill=(20, int(30 + y * 0.3), int(60 + y * 0.5)))
    # Play button triangle
    center_x, center_y = 240, 135
    draw.ellipse([(center_x - 45, center_y - 45), (center_x + 45, center_y + 45)], fill=(0, 215, 215))
    draw.polygon(
        [(center_x - 15, center_y - 25), (center_x - 15, center_y + 25), (center_x + 25, center_y)],
        fill=(20, 25, 40),
    )
    return img


def resolve_raylib_thumb_path() -> Optional[str]:
    """Finds raylib-thumb executable bundled with ATUI or in system PATH."""
    base_dir = Path(__file__).resolve().parent
    candidates = [
        base_dir / "bin" / ("raylib-thumb.exe" if os.name == "nt" else "raylib-thumb"),
        base_dir.parent / "tools" / "raylib_thumb" / ("raylib-thumb.exe" if os.name == "nt" else "raylib-thumb"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    found = shutil.which("raylib-thumb")
    if found:
        return found
    return None


def render_image_raylib(image_path: Path, max_width: int = 46, max_height: int = 20) -> Optional[Tuple[Text, str]]:
    """
    Renders an image thumbnail using the high-performance Raylib-Go engine
    (https://github.com/gen2brain/raylib-go).
    """
    raylib_bin = resolve_raylib_thumb_path()
    if not raylib_bin:
        return None

    try:
        res = subprocess.run(
            [raylib_bin, str(image_path), str(max_width), str(max_height)],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        if res.returncode == 0 and res.stdout:
            lines = res.stdout.splitlines()
            dim_str = "px (Raylib-Go)"
            ansi_lines = []
            for line in lines:
                if line.startswith("DIM:"):
                    dim_str = f"{line.split(':', 1)[1]} px (Raylib-Go)"
                else:
                    ansi_lines.append(line)
            ansi_content = "\n".join(ansi_lines)
            if ansi_content.strip():
                rendered = Text.from_ansi(ansi_content)
                return rendered, dim_str
    except Exception:
        pass
    return None


def load_image_thumbnail(
    remote_path: str,
    adb_manager,
    max_width: int = 46,
    max_height: int = 20,
) -> Tuple[Optional[Text], Optional[str]]:
    """Downloads or retrieves image and renders high-res half-block with Raylib-Go or Pillow."""
    cache_key = f"img_{remote_path}_{max_width}_{max_height}"
    if cache_key in _MEDIA_CACHE:
        return _MEDIA_CACHE[cache_key]

    if adb_manager.demo_mode:
        img = generate_demo_image(remote_path)
        rendered = render_image_halfblock(img, max_width, max_height)
        result = (rendered, "480x320 px (Demo)")
        _MEDIA_CACHE[cache_key] = result
        return result

    cache_file = get_cache_thumb_path()
    # Pull file to temp cache
    success, _ = adb_manager.pull_file(remote_path, str(cache_file.parent))
    target = cache_file.parent / Path(remote_path).name

    if not target.exists():
        return None, "Download fallito"

    # 1. Prioritize Raylib-Go accelerated rendering
    raylib_res = render_image_raylib(target, max_width, max_height)
    if raylib_res is not None:
        try:
            target.unlink()
        except Exception:
            pass
        _MEDIA_CACHE[cache_key] = raylib_res
        return raylib_res

    # 2. Pillow fallback
    if HAS_PILLOW:
        try:
            with Image.open(target) as img:
                dim_str = f"{img.width}x{img.height} px"
                text_render = render_image_halfblock(img, max_width, max_height)

            try:
                target.unlink()
            except Exception:
                pass

            result = (text_render, dim_str)
            _MEDIA_CACHE[cache_key] = result
            return result
        except Exception as e:
            try:
                target.unlink()
            except Exception:
                pass
            return None, f"Errore anteprima: {e}"

    try:
        target.unlink()
    except Exception:
        pass
    return None, "Nessun motore di rendering immagini disponibile"


def load_video_thumbnail(
    remote_path: str,
    adb_manager,
    max_width: int = 46,
    max_height: int = 20,
) -> Tuple[Optional[Text], Optional[str]]:
    """Extracts a frame from a remote video file using ffmpeg and renders high-res half-block."""
    if not HAS_PILLOW:
        return None, "Libreria Pillow non installata"

    cache_key = f"vid_{remote_path}_{max_width}_{max_height}"
    if cache_key in _MEDIA_CACHE:
        return _MEDIA_CACHE[cache_key]

    if adb_manager.demo_mode:
        img = generate_video_demo(remote_path)
        rendered = render_image_halfblock(img, max_width, max_height)
        result = (rendered, "1920x1080 px (Video Demo)")
        _MEDIA_CACHE[cache_key] = result
        return result

    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        return None, "FFmpeg non trovato sul computer"

    temp_thumb = get_cache_thumb_path(".vid_frame.jpg")
    if temp_thumb.exists():
        try:
            temp_thumb.unlink()
        except Exception:
            pass

    # Method 1: Stream the first 8MB directly from ADB into ffmpeg pipe
    serial = adb_manager.active_device.serial if adb_manager.active_device else ""
    adb_cmd = [adb_manager.adb_path]
    if serial:
        adb_cmd.extend(["-s", serial])
    adb_cmd.extend(["exec-out", f"head -c 8000000 '{remote_path}'"])

    ff_cmd = [
        ffmpeg_bin,
        "-y",
        "-i",
        "pipe:0",
        "-frames:v",
        "1",
        "-f",
        "image2",
        str(temp_thumb),
    ]

    try:
        p_adb = subprocess.Popen(
            adb_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        p_ff = subprocess.Popen(
            ff_cmd,
            stdin=p_adb.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        p_adb.stdout.close()
        p_ff.communicate(timeout=8)
    except Exception:
        pass

    if temp_thumb.exists():
        try:
            with Image.open(temp_thumb) as img:
                dim_str = f"{img.width}x{img.height} px (Frame Video)"
                text_render = render_image_halfblock(img, max_width, max_height)
            try:
                temp_thumb.unlink()
            except Exception:
                pass
            result = (text_render, dim_str)
            _MEDIA_CACHE[cache_key] = result
            return result
        except Exception:
            pass

    return None, "Impossibile estrarre anteprima video"


def generate_category_card(
    name: str,
    category: "FileCategory",
    ext: str = "",
) -> "Image.Image":
    """
    Generates a high-aesthetic, cyber-styled graphical card thumbnail for any file category,
    including a specialized default card with paperclip emblem (📎) for unrecognized files (e.g. prod.keys).
    """
    card_w, card_h = 400, 170
    img = Image.new("RGB", (card_w, card_h), color=(22, 22, 30))
    draw = ImageDraw.Draw(img)

    # Ambient vertical gradient background
    for y in range(card_h):
        ratio = y / float(card_h)
        r = int(18 + ratio * 8)
        g = int(20 + ratio * 10)
        b = int(32 + ratio * 16)
        draw.line([(0, y), (card_w, y)], fill=(r, g, b))

    # Outer border with rounded corners
    draw.rounded_rectangle([(4, 4), (card_w - 5, card_h - 5)], radius=8, outline=(41, 46, 66), width=2)

    cat_val = category.value if hasattr(category, "value") else str(category)
    ext_clean = (ext or (name.rsplit(".", 1)[-1] if "." in name else "")).upper()

    # Category styling definitions: (accent_rgb, top_title, badge_color)
    if cat_val == "apk":
        accent = (158, 206, 106)
        title = "ANDROID PACKAGE (.APK)"
        # Draw Android Robot Mascot
        head_box = [(175, 46), (225, 96)]
        draw.chord(head_box, start=180, end=0, fill=accent)
        # Antennas
        draw.line([(183, 49), (175, 36)], fill=accent, width=3)
        draw.line([(217, 49), (225, 36)], fill=accent, width=3)
        # Eyes
        draw.ellipse([(187, 58), (193, 64)], fill=(22, 22, 30))
        draw.ellipse([(207, 58), (213, 64)], fill=(22, 22, 30))
        # Body shoulders
        draw.rounded_rectangle([(172, 75), (228, 98)], radius=4, fill=accent)

    elif cat_val == "audio":
        accent = (187, 154, 247)
        title = f"AUDIO TRACK ({ext_clean or 'AUDIO'})"
        # Draw Equalizer Waveform bars
        bar_heights = [14, 26, 44, 58, 48, 64, 52, 60, 42, 30, 48, 36, 22, 12]
        start_x = 135
        for i, bh in enumerate(bar_heights):
            bx = start_x + i * 9
            y_top = 75 - (bh // 2)
            y_bot = 75 + (bh // 2)
            # Gradient bar
            draw.line([(bx, y_top), (bx, y_bot)], fill=accent if i % 2 == 0 else (122, 162, 247), width=5)

    elif cat_val == "document":
        accent = (122, 162, 247)
        title = f"DOCUMENT ({ext_clean or 'DOC'})"
        # Draw Document Sheet with folded corner
        draw.rectangle([(174, 38), (226, 98)], fill=(32, 36, 54), outline=accent, width=2)
        # Folded corner
        draw.polygon([(212, 38), (226, 52), (212, 52)], fill=accent)
        # Text lines
        draw.line([(182, 58), (206, 58)], fill=accent, width=2)
        draw.line([(182, 68), (218, 68)], fill=(169, 177, 214), width=2)
        draw.line([(182, 78), (218, 78)], fill=(169, 177, 214), width=2)
        draw.line([(182, 88), (202, 88)], fill=(86, 95, 137), width=2)

    elif cat_val == "archive":
        accent = (255, 158, 100)
        title = f"COMPRESSED ARCHIVE ({ext_clean or 'ZIP'})"
        # Draw Archive Box / Crate
        draw.rectangle([(168, 44), (232, 96)], fill=(36, 32, 42), outline=accent, width=2)
        # Box lid
        draw.rectangle([(164, 40), (236, 50)], fill=accent)
        # Zipper track
        for zy in range(54, 94, 6):
            draw.line([(196, zy), (204, zy)], fill=(255, 255, 255), width=2)

    elif cat_val == "code":
        accent = (115, 218, 202)
        title = f"SOURCE CODE ({ext_clean or 'CODE'})"
        # Draw Code Editor snippet
        draw.rounded_rectangle([(160, 40), (240, 96)], radius=4, fill=(26, 32, 44), outline=accent, width=2)
        # Editor header bar
        draw.rectangle([(162, 42), (238, 50)], fill=(36, 44, 60))
        draw.ellipse([(165, 44), (168, 47)], fill=(247, 118, 142))
        draw.ellipse([(171, 44), (174, 47)], fill=(224, 175, 104))
        draw.ellipse([(177, 44), (180, 47)], fill=(158, 206, 106))
        # Code lines
        draw.line([(168, 60), (196, 60)], fill=accent, width=2)
        draw.line([(174, 70), (220, 70)], fill=(122, 162, 247), width=2)
        draw.line([(174, 80), (210, 80)], fill=(187, 154, 247), width=2)
        draw.line([(168, 90), (180, 90)], fill=accent, width=2)

    elif cat_val == "system":
        accent = (157, 124, 216)
        title = f"SYSTEM / BINARY ({ext_clean or 'SYS'})"
        # Draw CPU Microchip
        draw.rectangle([(176, 46), (224, 94)], fill=(34, 30, 48), outline=accent, width=2)
        # Core die
        draw.rectangle([(186, 56), (214, 84)], fill=accent)
        # Radiating pins
        for py in (52, 64, 76, 88):
            draw.line([(168, py), (176, py)], fill=accent, width=2)
            draw.line([(224, py), (232, py)], fill=accent, width=2)
        for px in (186, 198, 204, 214):
            draw.line([(px, 38), (px, 46)], fill=accent, width=2)
            draw.line([(px, 94), (px, 102)], fill=accent, width=2)

    elif cat_val == "folder":
        accent = (224, 175, 104)
        title = "DIRECTORY FOLDER"
        # Draw Directory Folder
        draw.polygon([(166, 46), (196, 46), (206, 56), (234, 56), (234, 96), (166, 96)], fill=(38, 36, 44), outline=accent)
        draw.rectangle([(166, 58), (234, 96)], fill=accent)

    elif cat_val == "image":
        accent = (187, 154, 247)
        title = f"IMAGE PHOTO ({ext_clean or 'IMG'})"
        # Draw Photo frame with sunset & mountain
        draw.rectangle([(168, 42), (232, 96)], fill=(30, 32, 50), outline=accent, width=2)
        draw.ellipse([(178, 48), (192, 62)], fill=(255, 200, 100))
        draw.polygon([(170, 94), (195, 68), (220, 94)], fill=(75, 85, 120))
        draw.polygon([(190, 94), (212, 75), (230, 94)], fill=(55, 65, 95))

    elif cat_val == "video":
        accent = (125, 207, 255)
        title = f"VIDEO CLIP ({ext_clean or 'VID'})"
        # Draw Video Slate with play triangle
        draw.rectangle([(164, 44), (236, 96)], fill=(20, 30, 48), outline=accent, width=2)
        cx, cy = 200, 70
        draw.ellipse([(cx - 18, cy - 18), (cx + 18, cy + 18)], fill=accent)
        draw.polygon([(cx - 6, cy - 10), (cx - 6, cy + 10), (cx + 10, cy)], fill=(20, 30, 48))

    else:
        # DEFAULT / UNRECOGNIZED FILE TYPE (e.g. prod.keys, .dat, unrecognized extensions)
        accent = (192, 202, 245)
        title = f"GENERIC FILE [📎] ({ext_clean or 'FILE'})"

        # Draw a beautiful, sleek metallic Paperclip (📎)
        cx, cy = 200, 72
        w = 3
        # Outer top curve
        draw.arc([(cx - 20, cy - 34), (cx + 20, cy + 4)], start=180, end=0, fill=accent, width=w)
        # Left outer line down
        draw.line([(cx - 20, cy - 15), (cx - 20, cy + 24)], fill=accent, width=w)
        # Bottom outer curve
        draw.arc([(cx - 20, cy + 6), (cx + 20, cy + 42)], start=0, end=180, fill=accent, width=w)
        # Right outer line up
        draw.line([(cx + 20, cy - 15), (cx + 20, cy + 24)], fill=accent, width=w)
        # Inner top curve
        draw.arc([(cx - 10, cy - 22), (cx + 10, cy + 4)], start=180, end=0, fill=accent, width=w)
        # Left inner line down
        draw.line([(cx - 10, cy - 9), (cx - 10, cy + 18)], fill=accent, width=w)
        # Bottom inner curve
        draw.arc([(cx - 10, cy + 6), (cx + 10, cy + 32)], start=0, end=180, fill=accent, width=w)
        # Right inner line up
        draw.line([(cx + 10, cy + 4), (cx + 10, cy + 18)], fill=accent, width=w)

    # Top category banner header
    draw.rectangle([(6, 6), (card_w - 7, 27)], fill=(28, 30, 44))
    draw.text((16, 9), title, fill=accent)

    # Bottom file label badge
    draw.rounded_rectangle([(16, 126), (card_w - 17, 156)], radius=4, fill=(28, 32, 48), outline=(56, 64, 92), width=1)
    display_label = name if len(name) <= 36 else f"{name[:20]}...{name[-13:]}"
    draw.text((26, 134), display_label, fill=(240, 244, 255))
    if ext_clean:
        draw.text((card_w - 70, 134), f"[{ext_clean}]", fill=accent)

    return img


def get_file_thumbnail(
    entry,
    adb_manager,
    max_width: int = 46,
    max_height: int = 20,
) -> Tuple[Optional[Text], Optional[str]]:
    """
    Unified thumbnail retriever for ALL file categories.
    Renders actual high-res previews for images and videos, and renders custom cyber-graphic
    category cards with Pillow for all other types (including unrecognized files like prod.keys with 📎).
    """
    cat_val = entry.category.value if hasattr(entry.category, "value") else str(entry.category)
    has_raylib = bool(resolve_raylib_thumb_path())

    if not HAS_PILLOW and not (has_raylib and cat_val == "image"):
        return None, "Nessun motore thumbnail disponibile"

    cache_key = f"thumb_{entry.path}_{max_width}_{max_height}"
    if cache_key in _MEDIA_CACHE:
        return _MEDIA_CACHE[cache_key]

    # 1. Real Image handling
    if cat_val == "image" and not adb_manager.demo_mode:
        render, dim = load_image_thumbnail(entry.path, adb_manager, max_width, max_height)
        if render is not None:
            _MEDIA_CACHE[cache_key] = (render, dim)
            return render, dim

    # 2. Real Video handling
    if cat_val == "video" and not adb_manager.demo_mode:
        render, dim = load_video_thumbnail(entry.path, adb_manager, max_width, max_height)
        if render is not None:
            _MEDIA_CACHE[cache_key] = (render, dim)
            return render, dim

    # 3. Custom Category Banner Card for all types (APK, Audio, Doc, Archive, Code, System, Folder, Default/prod.keys)
    ext = getattr(entry, "extension", "")
    card_img = generate_category_card(entry.name, entry.category, ext=ext)
    card_render = render_image_halfblock(card_img, max_width=max_width, max_height=max_height)
    dim_desc = f"{cat_val.upper()} Card [400x170 px]"
    result = (card_render, dim_desc)
    _MEDIA_CACHE[cache_key] = result
    return result


def load_media_thumbnail(
    remote_path: str,
    adb_manager,
    is_video: bool = False,
    max_width: int = 46,
    max_height: int = 20,
) -> Tuple[Optional[Text], Optional[str]]:
    """Unified dispatcher for image and video high-res thumbnail previews."""
    video_mode = is_video is True or getattr(is_video, "value", None) == "video" or str(is_video).lower() == "video"
    if video_mode:
        return load_video_thumbnail(remote_path, adb_manager, max_width, max_height)
    return load_image_thumbnail(remote_path, adb_manager, max_width, max_height)


