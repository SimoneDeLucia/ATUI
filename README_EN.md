# ⚡ ATUI — Android Terminal User Interface

[🇮🇹 Italiano](README.md) | [🇬🇧 English](README_EN.md)

> **A powerful, modern, and reactive terminal file manager for Android devices via ADB, inspired by the Miller Columns aesthetics of [pikpaktui](https://github.com/Bengerthelorf/pikpaktui).**

> 🤖 **Development Disclaimer:** This application was vibecoded with **Google Antigravity**.

---

## 🌟 Key Features

- 🖱️ **Mouse-Clickable Checkbox Selection Squares**:
  - Dedicated `[✓]` column to select or deselect individual files directly with mouse clicks without moving the cursor or losing scroll position.
  - Clicking on the header `[✓]` instantly selects or deselects all files in the current folder.
- ⚡ **Direct File Opening (Double Click or Enter) Without Downloading**:
  - Instantly open and preview images, videos, PDFs, audio, and documents using your operating system's default viewer/application via double-click or `Enter`, seamlessly stored in temp cache without permanently cluttering local disk.
- 📊 **Graphical Footer Progress Bar for Transfers**:
  - Live progress visualization in the footer during downloads (`adb pull`), uploads (`adb push`), and device-to-device transfers.
- 🧭 **Quick Folders Section in Path Breadcrumbs Modal**:
  - Integrated quick jump buttons in the breadcrumbs navigation modal (`p`) for **Download**, **sdcard**, **MicroSD** (if detected), **DCIM**, and **Video**.
- 🖼️ **Graphic Card Thumbnails for ALL File Types**:
  - High-aesthetic 24-bit half-block cyber cards for all categories: **APK** (Android mascot), **Audio** (Equalizer waveform), **Documents** (Folio page), **Archives** (Zippered crate), **Source Code** (Console editor), **System/Binaries** (Microchip CPU).
  - **Default Thumbnail for Unrecognized File Formats**: Dedicated slate card with a paperclip emblem `📎` for unknown extensions (such as `prod.keys`), displaying format and file metadata.
  - High-resolution real image previews (JPG, PNG, HEIC, GIF, WEBP) and instant MP4 video frame extraction via FFmpeg.
- 🔄 **File Sorting by Name, Size, and Type (Mouse & Keyboard)**:
  - Click on table column headers (`Name`, `Size`, `Type`) to sort instantly with directional arrow indicators (`▲` / `▼`).
  - Keyboard controls: press `s` to cycle sort criterion (Name → Size → Type), press `S` (Shift+S) to invert sort order (Ascending ↔ Descending).
- 🖥️ **Integrated Real-Time Screen Mirroring via Scrcpy**:
  - Native integration with [scrcpy](https://github.com/genymobile/scrcpy) to mirror and control your Android screen at 60 FPS with ultra-low latency.
  - Launch with 1 click from the header `[ 🖥️ Scrcpy ]` button or with keyboard shortcut `m`.
  - Built-in guidance dialog (`ScrcpyModal`) if scrcpy is not detected on the computer.
- 📦 **Windows .msi Installer and Native Linux Compatibility**:
  - Configurable Windows `.msi` package (`installer/dist/AndroidTUI-Setup.msi` and `build_installer.ps1`) automatically downloading and registering official Google ADB USB drivers and platform-tools.
  - Complete Linux support: `atui` Linux binary launcher, `installer/51-android.rules` for non-root USB access, and `installer/install_linux.sh`.
- 🖥️ **3-Column Layout (Miller Columns)**:
  - **Parent Column**: Overview of parent folder with cursor-selectable `⬆️ ..` navigation item to move up seamlessly.
  - **Active Column**: Navigable directory list with category icons, checkboxes for batch operations, formatted sizes, permissions, and dates.
  - **Preview Column**: High-resolution ANSI cards, media previews, text viewer, and detailed metadata.
- 📱 **Device Header & Known Storage Locations**:
  - Live storage statistics: **Internal Storage** (`/sdcard`) and **External MicroSD** (`/storage/XXXX-XXXX`) with quick buttons and shortcut dialog (`g`).
- 🌐 **Full Bilingual Support (Italian / English)**:
  - Instant on-the-fly language toggle (`🌐 IT / 🌐 EN` button or `F2`).
- 🎨 **Modular CSS Architecture**:
  - Clean styling in `android_tui/css/` (`base.css`, `header.css`, `footer.css`, `browser.css`, `dashboard.css`, `modals.css`).

---

## ⌨️ Keyboard Shortcuts (Keybindings)

| Key | Action | Description |
| :---: | :--- | :--- |
| `j` / `↓` | **Down** | Move cursor down in file table / lists |
| `k` / `↑` | **Su** | Move cursor up in file table / lists |
| `Enter` / `l` | **Open** | Enter selected folder or initiate download for files |
| `Backspace` / `h` | **Parent** | Ascend to parent folder |
| `Space` | **Select** | Toggle batch selection for current item (keeps cursor row) |
| `a` | **Select All** | Select / deselect all files in current folder |
| `s` | **Sort** | Cycle sort criterion (Name → Size → Type) |
| `S` (Shift+S) | **Invert Order** | Invert sort order (Ascending ↔ Descending) |
| `m` | **Scrcpy** | Launch scrcpy screen mirroring for connected device |
| `Esc` | **Clear Selection** | Cancel batch multi-selection |
| `g` | **Storage Jump** | Open Quick Storage Jump dialog (Internal, MicroSD, DCIM, Downloads, Root) |
| `F2` | **Toggle Language** | Switch interface language between Italian and English |
| `d` | **Download to PC** | Download selected file(s) via `adb pull` |
| `u` | **Upload from PC** | Push file from computer to current phone folder via `adb push` |
| `f` | **New Folder** | Create a new folder on phone (`mkdir -p`) |
| `n` | **Rename** | Rename file or folder (`mv`) |
| `x` | **Delete** | Delete item(s) with confirmation modal (`rm -rf`) |
| `c` | **Devices** | Open ADB device selector modal |
| `Ctrl+D` | **Disconnect** | Disconnect current device and return to main dashboard |
| `r` | **Refresh** | Refresh directory view from ADB |
| `?` | **Help** | Open help cheatsheet modal |
| `q` | **Quit** | Exit AndroidTUI |

---

## 🚀 Installation & Getting Started

### ⚡ Method 1: Fast Windows Install (PowerShell One-Liner)
Run the following in **PowerShell**:
```powershell
irm https://raw.githubusercontent.com/SimoneDeLucia/ATUI/main/installer/install.ps1 | iex
```

---

### 📦 Method 2: Direct Windows Installer (.msi)
1. Download the official installer from [GitHub Releases](https://github.com/SimoneDeLucia/ATUI/releases):
   👉 **[Download AndroidTUI-Setup.msi](https://github.com/SimoneDeLucia/ATUI/releases/latest/download/AndroidTUI-Setup.msi)**
2. Double-click the `.msi` file. The wizard automatically configures:
   - AndroidTUI files in `Program Files`.
   - Global `atui` command in system `PATH`.
   - Official Google ADB USB Drivers and Platform-Tools.

---

### 🐍 Method 3: Manual Python pip Install
#### Requirements
- **Python 3.10+**
- **Android Debug Bridge (`adb`)**: included with Android Studio or standalone [SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools).
- **FFmpeg** (optional, recommended for MP4 video thumbnail previews).

```bash
git clone https://github.com/SimoneDeLucia/ATUI.git
cd ATUI
pip install -e .
```

### 3. Launch from Any Terminal
```bash
atui
```

Available command-line flags:
```bash
# Standard launch
atui

# Specify custom adb path
atui --adb-path "C:\path\to\adb.exe"

# Show help
atui --help
```

---

## 📜 License & Open Source Compliance

This project is free software licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See the [LICENSE](LICENSE) file for complete terms and conditions.

### 🤝 Third-Party Credits & Compliance
ATUI respects and complies with the attribution requirements of the open-source projects that inspired or power its capabilities:
- **[pikpaktui](https://github.com/Bengerthelorf/pikpaktui)** (Copyright (c) 2025 Bengerthelorf, **Apache 2.0** License): design and aesthetic inspiration for Miller Columns navigation and terminal interface layout.
- **[scrcpy](https://github.com/Genymobile/scrcpy)** (Copyright (c) 2018 Genymobile, **Apache 2.0** License): real-time Android screen mirroring engine, invoked as an external independent process.
- **[raylib-go](https://github.com/gen2brain/raylib-go)** (Copyright (c) Milan Nikolic & Ramon Santamaria, **zlib/libpng** License): high-performance purego terminal thumbnail rendering engine and bicubic image resampling (ANSI 24-bit halfblocks).

> ℹ️ **Legal Compatibility:** According to the Free Software Foundation (FSF), both the **Apache License 2.0** and the **zlib/libpng License** are fully compatible with GPLv3. All required attribution notices are preserved in the [NOTICE](NOTICE) file.



