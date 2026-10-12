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


# Textual CSS styling inspired by PikPakTUI
APP_CSS = """
Screen {
    background: #1a1b26;
    color: #c0caf5;
    layout: vertical;
}

#header-bar {
    dock: top;
    height: 3;
    background: #16161e;
    border-bottom: heavy #3d59a1;
    layout: horizontal;
    padding: 0 1;
    align: left middle;
}

#header-logo {
    width: 24;
    text-style: bold;
    color: #7dcfff;
}

#header-device-badge {
    width: auto;
    background: #24283b;
    color: #73daca;
    padding: 0 1;
    margin-right: 1;
    border: none;
    text-style: bold;
}

#header-stats {
    width: 1fr;
    color: #9aa5ce;
}

#header-path {
    width: auto;
    color: #e0af68;
    text-style: bold;
}

#footer-bar {
    dock: bottom;
    height: 3;
    background: #16161e;
    border-top: heavy #3d59a1;
    layout: horizontal;
    padding: 0 1;
    align: left middle;
}

#footer-keys {
    width: 1fr;
    color: #7aa2f7;
}

#footer-toast {
    width: auto;
    color: #73daca;
    text-style: bold;
    padding: 0 1;
}

/* Browser 3-Column Miller Panes */
#miller-container {
    height: 1fr;
    layout: horizontal;
    padding: 0;
}

.pane {
    height: 100%;
    border: round #3d59a1;
    background: #1a1b26;
    padding: 0;
}

.pane:focus-within {
    border: round #7dcfff;
}

#parent-pane {
    width: 25%;
    border: round #292e42;
    background: #16161e;
}

#current-pane {
    width: 45%;
    border: round #7dcfff;
}

#preview-pane {
    width: 30%;
    border: round #3d59a1;
    background: #16161e;
}

/* Disconnected Hero Dashboard */
#disconnected-container {
    height: 1fr;
    align: center middle;
    padding: 1 2;
    overflow-y: auto;
}

#disconnected-hero {
    width: 90;
    max-width: 96%;
    border: round #f7768e;
    background: #1f2335;
    padding: 1 2;
}

#hero-title {
    text-align: center;
    text-style: bold;
    color: #7dcfff;
    margin-bottom: 1;
}

#hero-subtitle {
    text-align: center;
    color: #f7768e;
    margin-bottom: 1;
}

.connection-options-grid {
    layout: horizontal;
    height: auto;
    margin-top: 1;
    margin-bottom: 1;
}

.option-card {
    width: 1fr;
    height: auto;
    border: round #414868;
    background: #24283b;
    padding: 1;
    margin: 0 1;
}

.option-card:hover {
    border: round #7dcfff;
    background: #292e42;
}

.card-title {
    text-style: bold;
    color: #73daca;
    margin-bottom: 1;
}

.card-desc {
    color: #9aa5ce;
    margin-bottom: 1;
}

/* Modals */
ModalScreen {
    align: center middle;
    background: rgba(0, 0, 0, 0.7);
}

.modal-dialog {
    width: 76;
    max-width: 90%;
    height: auto;
    border: round #7dcfff;
    background: #1f2335;
    padding: 1 2;
}

.modal-title {
    text-style: bold;
    color: #7dcfff;
    text-align: center;
    margin-bottom: 1;
}

.modal-subtitle {
    color: #9aa5ce;
    margin-bottom: 1;
}

.button-bar {
    layout: horizontal;
    align: right middle;
    margin-top: 1;
    height: 3;
}

Button {
    margin-left: 1;
    min-width: 12;
    background: #3d59a1;
    color: #c0caf5;
    border: none;
}

Button:hover {
    background: #7dcfff;
    color: #1a1b26;
    text-style: bold;
}

Button.-primary {
    background: #7aa2f7;
    color: #1a1b26;
    text-style: bold;
}

Button.-primary:hover {
    background: #7dcfff;
    color: #1a1b26;
}

Button.-danger {
    background: #f7768e;
    color: #1a1b26;
    text-style: bold;
}

Input {
    border: round #414868;
    background: #16161e;
    color: #c0caf5;
    margin-bottom: 1;
}

Input:focus {
    border: round #7dcfff;
}

/* Lists and Tables */
DataTable {
    background: transparent;
    height: 1fr;
}

DataTable > .datatable--header {
    background: #24283b;
    color: #7dcfff;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #33467c;
    color: #ffffff;
    text-style: bold;
}

ListView {
    background: transparent;
    height: 1fr;
}

ListItem {
    padding: 0 1;
}

ListItem.-selected {
    background: #33467c;
    color: #ffffff;
    text-style: bold;
}

/* Preview details */
#preview-content {
    padding: 0 1;
    height: 1fr;
    overflow-y: auto;
}

.meta-key {
    color: #7aa2f7;
    text-style: bold;
}

.meta-val {
    color: #c0caf5;
}
"""
