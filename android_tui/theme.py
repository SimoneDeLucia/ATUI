"""
Theme and visual styling for AndroidTUI.
Aesthetics inspired directly by pikpaktui:
- Modern dark slate palette (#1a1b26, #24283b)
- Cyber cyan/neon blue primary accents (#7dcfff, #00d7d7)
- Category-based file icons and harmonious colors
- Crisp rounded borders and micro-indicators
"""
from typing import Tuple
from .models import FileCategory, FileEntry


EXT_TO_CATEGORY = {
    # Archives
    "zip": FileCategory.ARCHIVE, "tar": FileCategory.ARCHIVE, "gz": FileCategory.ARCHIVE,
    "bz2": FileCategory.ARCHIVE, "xz": FileCategory.ARCHIVE, "rar": FileCategory.ARCHIVE,
    "7z": FileCategory.ARCHIVE, "zst": FileCategory.ARCHIVE, "tgz": FileCategory.ARCHIVE,
    "apk": FileCategory.APK, "xapk": FileCategory.APK, "apks": FileCategory.APK,
    # Images
    "jpg": FileCategory.IMAGE, "jpeg": FileCategory.IMAGE, "png": FileCategory.IMAGE,
    "gif": FileCategory.IMAGE, "svg": FileCategory.IMAGE, "webp": FileCategory.IMAGE,
    "bmp": FileCategory.IMAGE, "ico": FileCategory.IMAGE, "tiff": FileCategory.IMAGE,
    "tif": FileCategory.IMAGE, "heic": FileCategory.IMAGE, "heif": FileCategory.IMAGE,
    "avif": FileCategory.IMAGE,
    # Videos
    "mp4": FileCategory.VIDEO, "mkv": FileCategory.VIDEO, "avi": FileCategory.VIDEO,
    "mov": FileCategory.VIDEO, "wmv": FileCategory.VIDEO, "flv": FileCategory.VIDEO,
    "webm": FileCategory.VIDEO, "m4v": FileCategory.VIDEO, "ts": FileCategory.VIDEO,
    "3gp": FileCategory.VIDEO,
    # Audio
    "mp3": FileCategory.AUDIO, "flac": FileCategory.AUDIO, "wav": FileCategory.AUDIO,
    "aac": FileCategory.AUDIO, "ogg": FileCategory.AUDIO, "wma": FileCategory.AUDIO,
    "m4a": FileCategory.AUDIO, "opus": FileCategory.AUDIO,
    # Documents
    "pdf": FileCategory.DOCUMENT, "doc": FileCategory.DOCUMENT, "docx": FileCategory.DOCUMENT,
    "txt": FileCategory.DOCUMENT, "md": FileCategory.DOCUMENT, "rtf": FileCategory.DOCUMENT,
    "odt": FileCategory.DOCUMENT, "xls": FileCategory.DOCUMENT, "xlsx": FileCategory.DOCUMENT,
    "ppt": FileCategory.DOCUMENT, "pptx": FileCategory.DOCUMENT, "csv": FileCategory.DOCUMENT,
    "epub": FileCategory.DOCUMENT, "log": FileCategory.DOCUMENT,
    # Code / Scripts
    "py": FileCategory.CODE, "rs": FileCategory.CODE, "js": FileCategory.CODE,
    "ts": FileCategory.CODE, "go": FileCategory.CODE, "c": FileCategory.CODE,
    "cpp": FileCategory.CODE, "h": FileCategory.CODE, "java": FileCategory.CODE,
    "kt": FileCategory.CODE, "sh": FileCategory.CODE, "bash": FileCategory.CODE,
    "zsh": FileCategory.CODE, "json": FileCategory.CODE, "xml": FileCategory.CODE,
    "yaml": FileCategory.CODE, "yml": FileCategory.CODE, "toml": FileCategory.CODE,
    "ini": FileCategory.CODE, "prop": FileCategory.CODE, "conf": FileCategory.CODE,
    "sql": FileCategory.CODE, "html": FileCategory.CODE, "css": FileCategory.CODE,
    # System
    "so": FileCategory.SYSTEM, "bin": FileCategory.SYSTEM, "rc": FileCategory.SYSTEM,
    "img": FileCategory.SYSTEM, "dat": FileCategory.SYSTEM,
}


TEXT_EXTENSIONS = {
    "txt", "md", "csv", "log", "json", "xml", "yaml", "yml", "toml",
    "ini", "conf", "prop", "properties", "rc", "cfg", "env",
    "py", "rs", "js", "ts", "jsx", "tsx", "c", "cpp", "h", "hpp",
    "java", "kt", "go", "sh", "bash", "zsh", "sql", "html", "css",
    "php", "rb", "lua", "vcf", "ovpn", "diff", "patch"
}


def is_text_previewable(name: str, is_dir: bool) -> bool:
    if is_dir:
        return False
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return ext in TEXT_EXTENSIONS


def categorize_entry(name: str, is_dir: bool) -> FileCategory:
    if is_dir:
        return FileCategory.FOLDER
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return EXT_TO_CATEGORY.get(ext, FileCategory.DEFAULT)


CATEGORY_ICONS = {
    FileCategory.FOLDER: "📁",
    FileCategory.ARCHIVE: "📦",
    FileCategory.APK: "🤖",
    FileCategory.IMAGE: "🖼️ ",
    FileCategory.VIDEO: "🎬",
    FileCategory.AUDIO: "🎵",
    FileCategory.DOCUMENT: "📄",
    FileCategory.CODE: "💻",
    FileCategory.SYSTEM: "⚙️ ",
    FileCategory.DEFAULT: "📎",
}

CATEGORY_COLORS = {
    FileCategory.FOLDER: "#7dcfff",     # Light cyan / blue
    FileCategory.ARCHIVE: "#ff9e64",    # Warm orange
    FileCategory.APK: "#9ece6a",        # Android emerald green
    FileCategory.IMAGE: "#bb9af7",      # Lavender purple
    FileCategory.VIDEO: "#b4f9f8",      # Bright turquoise
    FileCategory.AUDIO: "#7aa2f7",      # Soft blue
    FileCategory.DOCUMENT: "#73daca",   # Mint green
    FileCategory.CODE: "#e0af68",       # Gold / yellow
    FileCategory.SYSTEM: "#565f89",     # Slate gray
    FileCategory.DEFAULT: "#c0caf5",    # Soft foreground
}


def get_icon(category: FileCategory) -> str:
    return CATEGORY_ICONS.get(category, "📎")


def get_color(category: FileCategory) -> str:
    return CATEGORY_COLORS.get(category, "#c0caf5")


from pathlib import Path

CSS_DIR = Path(__file__).parent / "css"
CSS_FILES = [
    CSS_DIR / "base.css",
    CSS_DIR / "header.css",
    CSS_DIR / "footer.css",
    CSS_DIR / "browser.css",
    CSS_DIR / "dashboard.css",
    CSS_DIR / "modals.css",
]


def get_app_css() -> str:
    """Reads aggregated stylesheet from the css/ folder."""
    app_css_file = CSS_DIR / "app.css"
    if app_css_file.exists():
        return app_css_file.read_text(encoding="utf-8")
    return "\n\n".join(f.read_text(encoding="utf-8") for f in CSS_FILES if f.exists())


# Backward-compatible reference loaded dynamically from the css/ directory
APP_CSS = get_app_css()

