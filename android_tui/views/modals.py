"""
Interactive Modals and Dialogs for AndroidTUI.
Provides popups for Wireless Pairing/Connect, Device Selection & Addition,
Download/Upload transfers, File management (rename/delete/new folder),
Path Breadcrumbs navigation, Settings and Keyboard shortcuts Help.
"""
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Any, Dict, Union
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Input, Button, ListView, ListItem, Label
from rich.text import Text

from ..models import AdbDevice, ConnectionType, DeviceState, FileEntry
from ..i18n import t, get_current_language


# -----------------------------------------------------------------
# 1. Wireless Connect Modal
# -----------------------------------------------------------------
class WirelessConnectModal(ModalScreen[Optional[str]]):
    """Modal to connect to an Android device via Wi-Fi IP and Port."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("modal_wifi_connect_title"), classes="modal-title")
            yield Static(
                t("modal_wifi_connect_subtitle"),
                classes="modal-subtitle",
            )
            yield Input(placeholder="192.168.1.x:5555", id="input-wifi-addr")
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_connect"), id="btn-submit", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit":
            val = self.query_one("#input-wifi-addr", Input).value.strip()
            self.dismiss(val if val else None)
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 2. Wireless Pair Modal
# -----------------------------------------------------------------
class WirelessPairModal(ModalScreen[Optional[tuple]]):
    """Modal to pair Android 11+ device using a 6-digit pairing code."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("modal_wifi_pair_title"), classes="modal-title")
            yield Static(
                t("modal_wifi_pair_subtitle"),
                classes="modal-subtitle",
            )
            yield Static(t("modal_wifi_pair_addr_label"))
            yield Input(placeholder="192.168.1.x:porta", id="input-pair-addr")
            yield Static(t("modal_wifi_pair_code_label"))
            yield Input(placeholder="123456", id="input-pair-code")
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_pair"), id="btn-submit", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit":
            addr = self.query_one("#input-pair-addr", Input).value.strip()
            code = self.query_one("#input-pair-code", Input).value.strip()
            if addr and code:
                self.dismiss((addr, code))
            else:
                self.dismiss(None)
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 3. Device Selection & Addition Modal
# -----------------------------------------------------------------
class DeviceSelectModal(ModalScreen[Any]):
    """Modal to select active device among connected USB / Wireless devices or add a new one."""

    def __init__(self, devices: List[AdbDevice], **kwargs):
        super().__init__(**kwargs)
        self.devices = devices

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("dev_select_title"), classes="modal-title")
            yield Static(t("dev_select_subtitle"), classes="modal-subtitle")

            if self.devices:
                with ListView(id="device-list"):
                    for idx, dev in enumerate(self.devices):
                        icon = "🔌" if dev.connection_type == ConnectionType.USB else (
                            "📶" if dev.connection_type == ConnectionType.WIRELESS else "🎮"
                        )
                        state_color = "#73daca" if dev.state == DeviceState.DEVICE else "#f7768e"
                        t_lbl = Text()
                        t_lbl.append(f"{icon} {dev.display_name} ", style="bold #c0caf5")
                        t_lbl.append(f"({dev.serial}) ", style="dim")
                        t_lbl.append(f"[{dev.state.value.upper()}]", style=f"bold {state_color}")
                        yield ListItem(Label(t_lbl), id=f"dev-item-{idx}")
            else:
                yield Static(f"[dim]{t('dev_no_devices')}[/]", classes="modal-subtitle")

            # Dedicated Add Device Section (always accessible via USB or WiFi)
            yield Static(f"[bold #7dcfff]{t('dev_add_section')}[/]", classes="meta-key")
            with Horizontal(classes="button-bar", id="device-add-bar"):
                yield Button(t("btn_scan_usb"), id="btn-add-usb")
                yield Button(t("btn_wifi_connect"), id="btn-add-wifi")
                yield Button(t("btn_wifi_pair"), id="btn-add-pair")

            with Horizontal(classes="button-bar"):
                if self.devices:
                    yield Button(t("btn_select"), id="btn-select", variant="primary")
                yield Button(t("btn_close"), id="btn-cancel")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.devices):
            self.dismiss(self.devices[idx])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-select":
            list_view = self.query(ListView)
            if list_view and list_view.first().highlighted_child:
                idx = list_view.first().index
                if idx is not None and 0 <= idx < len(self.devices):
                    self.dismiss(self.devices[idx])
                    return
            self.dismiss(None)
        elif btn_id == "btn-add-usb":
            self.dismiss("action:scan_usb")
        elif btn_id == "btn-add-wifi":
            self.dismiss("action:wifi_connect")
        elif btn_id == "btn-add-pair":
            self.dismiss("action:wifi_pair")
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 3b. Batch Delete Confirmation Modal
# -----------------------------------------------------------------
class BatchDeleteModal(ModalScreen[bool]):
    """Modal to confirm batch deletion of multiple selected files."""

    def __init__(self, entries: List[FileEntry], **kwargs):
        super().__init__(**kwargs)
        self.entries = entries

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("modal_batch_del_title"), classes="modal-title")
            names_preview = ", ".join(e.name for e in self.entries[:4])
            if len(self.entries) > 4:
                names_preview += f" {t('modal_and_more_files', count=len(self.entries) - 4)}"
            yield Static(
                t("modal_batch_del_desc", count=len(self.entries), names=names_preview),
                classes="modal-subtitle",
            )
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_delete_all", count=len(self.entries)), id="btn-delete", variant="error")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-delete")


# -----------------------------------------------------------------
# -----------------------------------------------------------------
# 4. Folder Picker Utility & Download / Pull Modal
# -----------------------------------------------------------------
def pick_folder_gui(initial_dir: str = "") -> Optional[str]:
    """Opens a native graphical OS folder picker dialog to select a directory on PC."""
    import sys, subprocess, os
    if sys.platform == "win32":
        try:
            init_clean = initial_dir.replace("'", "''") if initial_dir else ""
            ps_script = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
                "$f.Description = 'Destination folder'; "
                + (f"$f.SelectedPath = '{init_clean}'; " if init_clean else "")
                + "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $f.SelectedPath }"
            )
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                creationflags=creation_flags,
            )
            out = res.stdout.strip()
            return out if out and os.path.isdir(out) else None
        except Exception:
            return None
    else:
        try:
            import tkinter
            from tkinter import filedialog
            root = tkinter.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            folder = filedialog.askdirectory(initialdir=initial_dir or str(Path.home()))
            root.destroy()
            return folder if folder and os.path.isdir(folder) else None
        except Exception:
            return None


def pick_files_gui(initial_dir: str = "") -> List[str]:
    """Opens a native graphical OS file picker dialog to select one or multiple files on PC."""
    if sys.platform == "win32":
        try:
            init_clean = initial_dir.replace("'", "''") if initial_dir else ""
            ps_script = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$f = New-Object System.Windows.Forms.OpenFileDialog; "
                "$f.Multiselect = $true; "
                "$f.Title = 'Seleziona file da caricare'; "
                + (f"$f.InitialDirectory = '{init_clean}'; " if init_clean else "")
                + "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $f.FileNames }"
            )
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                creationflags=creation_flags,
            )
            lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            return [p for p in lines if os.path.exists(p)]
        except Exception:
            return []
    else:
        try:
            import tkinter
            from tkinter import filedialog
            root = tkinter.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            files = list(filedialog.askopenfilenames(initialdir=initial_dir or str(Path.home())))
            root.destroy()
            return [f for f in files if os.path.exists(f)]
        except Exception:
            return []


def parse_file_paths(raw_input: str) -> List[str]:
    """Parses one or multiple local file/folder paths from input text,
    stripping quotes (e.g. from Windows Explorer 'Copy as path'),
    resolving newlines, semicolons, and space-separated quoted paths.
    """
    if not raw_input:
        return []

    text = raw_input.strip()
    if not text:
        return []

    paths: List[str] = []

    # If newlines exist, process line by line
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) > 1:
        for line in lines:
            line_clean = line.strip().strip('"\'').strip()
            if line_clean:
                paths.append(line_clean)
        return list(dict.fromkeys(paths))

    # If there are semicolons, split by semicolon
    if ";" in text:
        for part in text.split(";"):
            clean = part.strip().strip('"\'').strip()
            if clean:
                paths.append(clean)
        return list(dict.fromkeys(paths))

    # Check for multiple quoted paths on a single line: e.g. "path1" "path2"
    quoted_matches = re.findall(r'["\']([^"\']+)["\']', text)
    if len(quoted_matches) >= 2:
        return list(dict.fromkeys([m.strip() for m in quoted_matches if m.strip()]))
    elif len(quoted_matches) == 1 and text.startswith(('"', "'")) and text.endswith(('"', "'")):
        return [quoted_matches[0].strip()]

    # Otherwise, clean single line stripped of quotes
    clean = text.strip('"\'').strip()
    return [clean] if clean else []


class DownloadModal(ModalScreen[Optional[str]]):
    """Modal to download selected file or folder from Phone to PC."""

    def __init__(self, remote_name: str, remote_path: str, default_pc_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.remote_name = remote_name
        self.remote_path = remote_path
        self.default_pc_dir = default_pc_dir

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("modal_dl_title"), classes="modal-title")
            yield Static(
                t("modal_dl_subtitle", path=self.remote_path),
                classes="modal-subtitle",
            )
            with Horizontal(classes="folder-input-row"):
                yield Input(value=self.default_pc_dir, id="input-pc-dest")
                yield Button(t("btn_browse_pc"), id="btn-browse-pc-gui", variant="primary")
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_download_now"), id="btn-submit", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit":
            val = self.query_one("#input-pc-dest", Input).value.strip()
            self.dismiss(val if val else None)
        elif event.button.id == "btn-browse-pc-gui":
            cur_val = self.query_one("#input-pc-dest", Input).value.strip() or self.default_pc_dir
            chosen = pick_folder_gui(cur_val)
            if chosen:
                self.query_one("#input-pc-dest", Input).value = chosen
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 4b. Batch Download Modal
# -----------------------------------------------------------------
class BatchDownloadModal(ModalScreen[Optional[str]]):
    """Modal to confirm batch downloading multiple selected files."""

    def __init__(self, entries: List[FileEntry], default_pc_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.entries = entries
        self.default_pc_dir = default_pc_dir

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("modal_batch_dl_title"), classes="modal-title")
            total_bytes = sum(e.size for e in self.entries if not e.is_dir)
            total_str = self._format_size(total_bytes)
            names_preview = ", ".join(e.name for e in self.entries[:4])
            if len(self.entries) > 4:
                names_preview += f" {t('modal_and_more_files', count=len(self.entries) - 4)}"

            yield Static(
                t("modal_batch_dl_subtitle", count=len(self.entries), size=total_str, names=names_preview),
                classes="modal-subtitle",
            )
            with Horizontal(classes="folder-input-row"):
                yield Input(value=self.default_pc_dir, id="input-pc-dest")
                yield Button(t("btn_browse_pc"), id="btn-browse-pc-gui", variant="primary")
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_download_all", count=len(self.entries)), id="btn-submit", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def _format_size(self, size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit":
            val = self.query_one("#input-pc-dest", Input).value.strip()
            self.dismiss(val if val else None)
        elif event.button.id == "btn-browse-pc-gui":
            cur_val = self.query_one("#input-pc-dest", Input).value.strip() or self.default_pc_dir
            chosen = pick_folder_gui(cur_val)
            if chosen:
                self.query_one("#input-pc-dest", Input).value = chosen
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 4c. Unified Download & Device-to-Device Transfer Modal
# -----------------------------------------------------------------
class DownloadDestinationModal(ModalScreen[Optional[Tuple[str, str, Optional[AdbDevice]]]]):
    """
    Modal allowing the user to download files to the local PC or directly transfer
    them between two connected Android devices with interactive folder navigation.
    """

    def __init__(
        self,
        entries: List[FileEntry],
        default_pc_dir: str,
        available_devices: List[AdbDevice],
        active_device: Optional[AdbDevice] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.entries = entries
        self.default_pc_dir = default_pc_dir
        self.other_devices = [
            d for d in available_devices
            if active_device and d.serial != active_device.serial and d.state == DeviceState.DEVICE
        ]
        self.selected_target_device: Optional[AdbDevice] = self.other_devices[0] if self.other_devices else None
        self.mode: str = "pc"

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("transfer_title"), classes="modal-title")
            summary_txt = f"{len(self.entries)} {t('transfer_items_suffix')}" if len(self.entries) > 1 else (self.entries[0].name if self.entries else "")
            yield Static(f"[dim]{t('transfer_item_prefix')}: [bold #7dcfff]{summary_txt}[/][/]", classes="modal-subtitle")

            # Selection buttons between PC and Android
            with Horizontal(classes="button-bar", id="d2d-choice-bar"):
                yield Button(t("transfer_mode_pc"), id="btn-choice-pc", variant="primary")
                has_devs = bool(self.other_devices)
                dev_btn_lbl = t("transfer_mode_device")
                if not has_devs:
                    dev_btn_lbl += f" ({t('transfer_no_second_device_short')})"
                yield Button(dev_btn_lbl, id="btn-choice-device", disabled=not has_devs)

            # Section PC Destination
            with Vertical(id="section-pc-dest"):
                yield Static(t("transfer_pc_dir"), classes="meta-key")
                with Horizontal(classes="folder-input-row"):
                    yield Input(value=self.default_pc_dir, id="input-pc-dest")
                    yield Button(t("btn_browse_pc"), id="btn-browse-pc-gui", variant="primary")
                with Horizontal(classes="quick-folders-bar"):
                    yield Button("📥 Downloads", id="btn-q-pc-dl")
                    yield Button("🖥️ Desktop", id="btn-q-pc-dt")
                    yield Button("📁 Documenti", id="btn-q-pc-doc")
                    yield Button("🏠 Home", id="btn-q-pc-home")

            # Section Device Destination
            with Vertical(id="section-device-dest"):
                if self.other_devices:
                    yield Static(t("transfer_select_device"), classes="meta-key")
                    with ListView(id="target-device-list"):
                        for idx, d in enumerate(self.other_devices):
                            icon = "🔌" if d.connection_type == ConnectionType.USB else "📶"
                            t_lbl = Text()
                            t_lbl.append(f"{icon} {d.display_name} ", style="bold #73daca")
                            t_lbl.append(f"({d.serial})", style="dim")
                            yield ListItem(Label(t_lbl), id=f"target-dev-{idx}")
                    yield Static(t("transfer_remote_dir"), classes="meta-key")
                    with Horizontal(classes="folder-input-row"):
                        yield Input(value="/sdcard/Download", id="input-remote-dest")
                        yield Button(t("btn_new_folder"), id="btn-d2d-mkdir")
                    with Horizontal(classes="quick-folders-bar"):
                        yield Button("📥 /sdcard/Download", id="btn-q-dev-dl")
                        yield Button("📱 /sdcard", id="btn-q-dev-sd")
                        yield Button("📷 /sdcard/DCIM", id="btn-q-dev-dcim")
                else:
                    yield Static(f"[bold #f7768e]{t('transfer_no_second_device')}[/]", classes="modal-subtitle")

            with Horizontal(classes="button-bar"):
                yield Button(t("transfer_btn_start"), id="btn-submit", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_mount(self) -> None:
        self.query_one("#section-device-dest").display = False
        self.query_one("#section-pc-dest").display = True

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.other_devices):
            self.selected_target_device = self.other_devices[idx]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-choice-pc":
            self.mode = "pc"
            self.query_one("#btn-choice-pc", Button).variant = "primary"
            self.query_one("#btn-choice-device", Button).variant = "default"
            self.query_one("#section-pc-dest").display = True
            self.query_one("#section-device-dest").display = False
        elif btn_id == "btn-choice-device":
            if self.other_devices:
                self.mode = "device"
                self.query_one("#btn-choice-device", Button).variant = "primary"
                self.query_one("#btn-choice-pc", Button).variant = "default"
                self.query_one("#section-pc-dest").display = False
                self.query_one("#section-device-dest").display = True
        elif btn_id == "btn-browse-pc-gui":
            cur_val = self.query_one("#input-pc-dest", Input).value.strip() or self.default_pc_dir
            chosen = pick_folder_gui(cur_val)
            if chosen:
                self.query_one("#input-pc-dest", Input).value = chosen
        elif btn_id == "btn-d2d-mkdir":
            def on_created_folder(folder_name: Optional[str]) -> None:
                if folder_name:
                    cur = self.query_one("#input-remote-dest", Input).value.rstrip("/")
                    self.query_one("#input-remote-dest", Input).value = f"{cur}/{folder_name.strip()}"
            self.app.push_screen(CreateFolderModal(), on_created_folder)
        elif btn_id == "btn-q-pc-dl":
            self.query_one("#input-pc-dest", Input).value = str(Path.home() / "Downloads")
        elif btn_id == "btn-q-pc-dt":
            self.query_one("#input-pc-dest", Input).value = str(Path.home() / "Desktop")
        elif btn_id == "btn-q-pc-doc":
            self.query_one("#input-pc-dest", Input).value = str(Path.home() / "Documents")
        elif btn_id == "btn-q-pc-home":
            self.query_one("#input-pc-dest", Input).value = str(Path.home())
        elif btn_id == "btn-q-dev-dl":
            self.query_one("#input-remote-dest", Input).value = "/sdcard/Download"
        elif btn_id == "btn-q-dev-sd":
            self.query_one("#input-remote-dest", Input).value = "/sdcard"
        elif btn_id == "btn-q-dev-dcim":
            self.query_one("#input-remote-dest", Input).value = "/sdcard/DCIM"
        elif btn_id == "btn-submit":
            if self.mode == "pc":
                pc_dir = self.query_one("#input-pc-dest", Input).value.strip() or self.default_pc_dir
                self.dismiss(("pc", pc_dir, None))
            else:
                remote_dir = self.query_one("#input-remote-dest", Input).value.strip() or "/sdcard/Download"
                target = self.selected_target_device or (self.other_devices[0] if self.other_devices else None)
                self.dismiss(("device", remote_dir, target))
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 5. Upload / Push Modal
# -----------------------------------------------------------------
class UploadModal(ModalScreen[Optional[Union[List[str], Tuple[List[str], str]]]]):
    """Revamped modal to upload local file(s) or folder(s) from PC to Phone,
    supporting destination path customization, subfolder navigation,
    multiple selection, native file dialogs, and quoted paths from Explorer.
    """

    def __init__(self, current_phone_dir: str, device: Optional[AdbDevice] = None, **kwargs):
        super().__init__(**kwargs)
        self.current_phone_dir = current_phone_dir or "/sdcard/Download"
        self.device = device
        self.selected_files: List[str] = []

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog", id="upload-modal-dialog"):
            yield Static(t("modal_upload_title"), classes="modal-title")
            
            yield Static(t("modal_upload_dest_label"), classes="meta-key")
            with Horizontal(id="upload-dest-row", classes="folder-input-row"):
                yield Button(f"📂 {self.current_phone_dir}", id="btn-dest-path", classes="dest-path-button")
                yield Button(t("btn_change_dest"), id="btn-change-dest", variant="primary")

            yield Static(t("modal_upload_src_label"), classes="meta-key")
            with Horizontal(classes="folder-input-row"):
                yield Input(placeholder=t("modal_upload_placeholder"), id="input-pc-src")
                yield Button(t("btn_add_paths"), id="btn-add-paths")

            with Horizontal(id="upload-actions-bar"):
                yield Button(t("btn_browse_files_gui"), id="btn-browse-files-gui", variant="primary")
                yield Button(t("btn_browse_folder_gui"), id="btn-browse-folder-gui", variant="default")
                yield Button("📥 Downloads", id="btn-q-ul-dl")
                yield Button("🖥️ Desktop", id="btn-q-ul-dt")

            with Vertical(id="upload-selected-container"):
                with Horizontal(id="upload-selected-header"):
                    yield Static(t("modal_upload_selected_label", count=0), id="upload-selected-title")
                    yield Button(t("btn_clear_list"), id="btn-clear-selected", variant="error")
                with VerticalScroll(id="upload-files-scroll"):
                    yield Static("", id="upload-files-list-text")

            with Horizontal(classes="button-bar"):
                yield Button(t("btn_upload_now"), id="btn-submit", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_mount(self) -> None:
        self._refresh_selected_display()

    def _refresh_selected_display(self) -> None:
        cont = self.query_one("#upload-selected-container")
        if not self.selected_files:
            cont.display = False
            return
        cont.display = True
        title = self.query_one("#upload-selected-title", Static)
        title.update(t("modal_upload_selected_label", count=len(self.selected_files)))

        lines = []
        for p in self.selected_files:
            fname = os.path.basename(p) or p
            if os.path.isdir(p):
                lines.append(f"[bold #7dcfff]📁 {fname}[/] [dim]({p})[/]")
            else:
                sz_str = ""
                try:
                    if os.path.exists(p):
                        sz = os.path.getsize(p)
                        sz_str = self._format_size(sz)
                except Exception:
                    pass
                sz_part = f" [dim]({sz_str})[/]" if sz_str else ""
                lines.append(f"[bold #73daca]📄 {fname}[/]{sz_part} [dim]— {p}[/]")
        self.query_one("#upload-files-list-text", Static).update("\n".join(lines))

    def _format_size(self, size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _add_paths(self, new_paths: List[str]) -> None:
        added = False
        for p in new_paths:
            c = p.strip().strip('"\'')
            if c and c not in self.selected_files:
                self.selected_files.append(c)
                added = True
        if added:
            self._refresh_selected_display()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._confirm_and_submit()

    def _open_destination_picker(self) -> None:
        def on_path_selected(target_path: Optional[str]) -> None:
            if target_path:
                self.current_phone_dir = target_path
                self._update_dest_display()

        dev = self.device or getattr(getattr(self.app, "adb", None), "active_device", None)
        self.app.push_screen(
            PathBreadcrumbsModal(current_path=self.current_phone_dir, device=dev),
            on_path_selected,
        )

    def _update_dest_display(self) -> None:
        try:
            btn = self.query_one("#btn-dest-path", Button)
            btn.label = f"📂 {self.current_phone_dir}"
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-submit":
            self._confirm_and_submit()
        elif btn_id == "btn-cancel":
            self.dismiss(None)
        elif btn_id in ("btn-dest-path", "btn-change-dest"):
            self._open_destination_picker()
        elif btn_id == "btn-add-paths":
            inp = self.query_one("#input-pc-src", Input)
            val = inp.value.strip()
            if val:
                paths = parse_file_paths(val)
                self._add_paths(paths)
                inp.value = ""
        elif btn_id == "btn-browse-files-gui":
            cur = self.query_one("#input-pc-src", Input).value.strip().strip('"\'')
            init_dir = cur if cur and os.path.isdir(cur) else (os.path.dirname(cur) if cur and os.path.isfile(cur) else "")
            chosen = pick_files_gui(init_dir)
            if chosen:
                self._add_paths(chosen)
        elif btn_id == "btn-browse-folder-gui":
            cur = self.query_one("#input-pc-src", Input).value.strip().strip('"\'')
            init_dir = cur if cur and os.path.isdir(cur) else ""
            chosen = pick_folder_gui(init_dir)
            if chosen:
                self._add_paths([chosen])
        elif btn_id == "btn-q-ul-dl":
            dl_dir = str(Path.home() / "Downloads")
            chosen = pick_files_gui(dl_dir)
            if chosen:
                self._add_paths(chosen)
            else:
                self.query_one("#input-pc-src", Input).value = dl_dir
        elif btn_id == "btn-q-ul-dt":
            dt_dir = str(Path.home() / "Desktop")
            chosen = pick_files_gui(dt_dir)
            if chosen:
                self._add_paths(chosen)
            else:
                self.query_one("#input-pc-src", Input).value = dt_dir
        elif btn_id == "btn-clear-selected":
            self.selected_files.clear()
            self._refresh_selected_display()

    def _confirm_and_submit(self) -> None:
        inp_val = self.query_one("#input-pc-src", Input).value.strip()
        all_paths = list(self.selected_files)
        if inp_val:
            for p in parse_file_paths(inp_val):
                c = p.strip().strip('"\'')
                if c and c not in all_paths:
                    all_paths.append(c)

        if all_paths:
            self.dismiss((all_paths, self.current_phone_dir))
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 6. Create Folder Modal
# -----------------------------------------------------------------
class CreateFolderModal(ModalScreen[Optional[str]]):
    """Modal to create a new folder on Phone."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("modal_mkdir_title"), classes="modal-title")
            yield Static(t("modal_mkdir_subtitle"), classes="modal-subtitle")
            yield Input(placeholder=t("modal_mkdir_placeholder"), id="input-folder-name")
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_create"), id="btn-submit", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit":
            val = self.query_one("#input-folder-name", Input).value.strip()
            self.dismiss(val if val else None)
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 7. Rename Modal
# -----------------------------------------------------------------
class RenameModal(ModalScreen[Optional[str]]):
    """Modal to rename an existing item on Phone."""

    def __init__(self, current_name: str, **kwargs):
        super().__init__(**kwargs)
        self.current_name = current_name

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("modal_rename_title"), classes="modal-title")
            yield Static(t("modal_rename_subtitle", name=self.current_name), classes="modal-subtitle")
            yield Input(value=self.current_name, id="input-rename")
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_rename"), id="btn-submit", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit":
            val = self.query_one("#input-rename", Input).value.strip()
            self.dismiss(val if val else None)
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 8. Delete Confirm Modal
# -----------------------------------------------------------------
class DeleteConfirmModal(ModalScreen[bool]):
    """Modal to confirm deletion of a file or folder."""

    def __init__(self, target_path: str, is_dir: bool, **kwargs):
        super().__init__(**kwargs)
        self.target_path = target_path
        self.is_dir = is_dir

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("modal_del_title"), classes="modal-title")
            kind = t("modal_del_kind_dir") if self.is_dir else t("modal_del_kind_file")
            yield Static(
                t("modal_del_subtitle", kind=kind, path=self.target_path),
                classes="modal-subtitle",
            )
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_delete_confirm"), id="btn-delete", variant="error")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-delete")


# -----------------------------------------------------------------
# 9. Help Modal (PikPakTUI-inspired cheatsheet)
# -----------------------------------------------------------------
class HelpModal(ModalScreen[None]):
    """Modal showing all keyboard shortcuts, Raylib-Go thumbnail engine, and ADB tips."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("help_modal_title"), classes="modal-title")
            yield Static(t("help_modal_content"), classes="modal-subtitle")
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_close"), id="btn-close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


# -----------------------------------------------------------------
# 10. Quick Storage Jump Modal
# -----------------------------------------------------------------
class QuickJumpModal(ModalScreen[Optional[str]]):
    """Modal to quickly jump to known storage locations without redundant icons."""

    def __init__(self, device: Optional[AdbDevice], **kwargs):
        super().__init__(**kwargs)
        self.device = device
        self.locations: List[Tuple[str, str, str]] = []

        free_suffix = t("quick_jump_free_suffix")

        # 1. Internal Storage
        int_free = f" ({device.storage_free} {free_suffix})" if device and device.storage_free else ""
        int_lbl = f"{t('quick_jump_internal')}: /sdcard{int_free}"
        self.locations.append((int_lbl, "/sdcard", "📱"))

        # 2. External MicroSD (Only present if device has an external MicroSD!)
        if device and device.ext_sd_path:
            sd_free = f" ({device.ext_sd_free} {free_suffix})" if device.ext_sd_free else ""
            sd_lbl = f"{t('quick_jump_microsd')}: {device.ext_sd_path}{sd_free}"
            self.locations.append((sd_lbl, device.ext_sd_path, "💾"))

        # 3. Downloads
        self.locations.append((f"{t('quick_jump_downloads')}: /sdcard/Download", "/sdcard/Download", "📥"))

        # 4. Photos / Camera (DCIM)
        self.locations.append((f"{t('quick_jump_dcim')}: /sdcard/DCIM", "/sdcard/DCIM", "📷"))

        # 5. Pictures
        self.locations.append((f"{t('quick_jump_pictures')}: /sdcard/Pictures", "/sdcard/Pictures", "🖼️"))

        # 6. System Root
        self.locations.append((f"{t('quick_jump_root')}: /", "/", "⚙️"))

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("modal_jump_title"), classes="modal-title")
            yield Static(t("modal_jump_desc"), classes="modal-subtitle")
            with ListView(id="jump-list"):
                for idx, (label, path, icon) in enumerate(self.locations):
                    t_text = Text()
                    t_text.append(f"{icon} ", style="bold #7dcfff")
                    t_text.append(label, style="bold #c0caf5" if path else "dim #565f89")
                    yield ListItem(Label(t_text), id=f"jump-item-{idx}")
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_select"), id="btn-select", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.locations):
            _, path, _ = self.locations[idx]
            if path:
                self.dismiss(path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-select":
            list_view = self.query_one("#jump-list", ListView)
            idx = list_view.index
            if idx is not None and 0 <= idx < len(self.locations):
                _, path, _ = self.locations[idx]
                if path:
                    self.dismiss(path)
                    return
            self.dismiss(None)
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 11. Path Breadcrumbs & Subfolders Modal
# -----------------------------------------------------------------
class PathBreadcrumbsModal(ModalScreen[Optional[str]]):
    """
    Interactive Breadcrumbs Modal allowing the user to select any folder or subfolder
    along the current directory hierarchy or manually input/paste a custom destination path,
    as well as quick jumps to standard folders (Download, sdcard, MicroSD, DCIM, Video).
    """

    def __init__(self, current_path: str, device: Optional[AdbDevice] = None, **kwargs):
        super().__init__(**kwargs)
        self.current_path = current_path or "/"
        self.device = device
        self.segments: List[Tuple[str, str]] = self._build_segments(self.current_path)
        self.subfolder_items: List[Tuple[str, str]] = []

    def _build_segments(self, path: str) -> List[Tuple[str, str]]:
        clean = "/" + path.strip("/") if path.strip("/") else "/"
        parts = [p for p in clean.split("/") if p]

        segments = [(t("breadcrumb_root"), "/")]
        accum = ""
        for p in parts:
            accum += "/" + p
            segments.append((f"📂 {p} ({accum})", accum))
        return segments

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("breadcrumb_title"), classes="modal-title")
            yield Static(t("breadcrumb_subtitle"), classes="modal-subtitle")

            with ListView(id="breadcrumb-list"):
                for idx, (label, target_path) in enumerate(self.segments):
                    t_lbl = Text()
                    is_current = (target_path == self.current_path.rstrip("/") or (target_path == "/" and self.current_path == "/"))
                    if is_current:
                        t_lbl.append("📍 ", style="bold #73daca")
                        t_lbl.append(label, style="bold #73daca underline")
                        curr_tag = f" [{t('breadcrumb_current_folder')}]"
                        t_lbl.append(curr_tag, style="dim #73daca")
                    else:
                        t_lbl.append("📁 ", style="bold #7dcfff")
                        t_lbl.append(label, style="bold #c0caf5")
                    yield ListItem(Label(t_lbl), id=f"bc-item-{idx}")

            # Child Subfolders Section (if any direct subdirectories exist)
            child_dirs = []
            try:
                adb = getattr(self.app, "adb", None)
                if adb:
                    entries, _ = adb.list_directory(self.current_path)
                    if entries:
                        for e in entries:
                            if e.is_dir and not e.name.startswith("."):
                                child_dirs.append((f"📂 {e.name}", e.path))
            except Exception:
                pass
            self.subfolder_items = child_dirs

            if self.subfolder_items:
                yield Static(f"[bold #7dcfff]{t('breadcrumb_subfolders_label')}[/]", classes="meta-key")
                with ListView(id="subfolder-list"):
                    for s_idx, (s_label, s_path) in enumerate(self.subfolder_items):
                        t_sub = Text()
                        t_sub.append("📁 ", style="bold #73daca")
                        t_sub.append(s_label.replace("📂 ", ""), style="bold #c0caf5")
                        t_sub.append(f" ({s_path})", style="dim")
                        yield ListItem(Label(t_sub), id=f"subfolder-item-{s_idx}")

            # Quick Folders Jump Section (Download, sdcard, MicroSD, DCIM, Video)
            yield Static(f"[bold #7dcfff]{t('breadcrumb_quick_locations')}[/]", classes="meta-key")
            with Horizontal(classes="quick-folders-bar", id="quick-folders-bar"):
                yield Button(f"📥 {t('quick_folder_dl')}", id="qf-download")
                yield Button(f"📱 {t('quick_folder_sd')}", id="qf-sdcard")
                if self.device and self.device.ext_sd_path:
                    yield Button(f"💾 {t('quick_folder_msd')}", id="qf-microsd")
                yield Button(f"📷 {t('quick_folder_dcim')}", id="qf-dcim")
                yield Button(f"🎬 {t('quick_folder_video')}", id="qf-video")

            yield Static(f"[bold #7dcfff]{t('breadcrumb_input_placeholder')}:[/]", classes="meta-key")
            yield Input(value=self.current_path, id="input-custom-path", placeholder="/sdcard/...")

            with Horizontal(classes="button-bar"):
                yield Button(t("breadcrumb_btn_go"), id="btn-go", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        lv_id = event.list_view.id
        idx = event.list_view.index
        if lv_id == "breadcrumb-list" and idx is not None and 0 <= idx < len(self.segments):
            _, target_path = self.segments[idx]
            self.dismiss(target_path)
        elif lv_id == "subfolder-list" and idx is not None and 0 <= idx < len(self.subfolder_items):
            _, target_path = self.subfolder_items[idx]
            self.dismiss(target_path)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        if val:
            self.dismiss(val)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "qf-download":
            self.dismiss("/sdcard/Download")
        elif btn_id == "qf-sdcard":
            self.dismiss("/sdcard")
        elif btn_id == "qf-microsd":
            if self.device and self.device.ext_sd_path:
                self.dismiss(self.device.ext_sd_path)
            else:
                self.dismiss("/storage")
        elif btn_id == "qf-dcim":
            self.dismiss("/sdcard/DCIM")
        elif btn_id == "qf-video":
            self.dismiss("/sdcard/Movies")
        elif btn_id == "btn-go":
            input_val = self.query_one("#input-custom-path", Input).value.strip()
            if input_val and input_val != self.current_path:
                self.dismiss(input_val)
                return
            try:
                list_view = self.query_one("#breadcrumb-list", ListView)
                idx = list_view.index
                if idx is not None and 0 <= idx < len(self.segments):
                    _, target_path = self.segments[idx]
                    self.dismiss(target_path)
                    return
            except Exception:
                pass
            self.dismiss(input_val if input_val else self.current_path)
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 12. Scrcpy Screen Mirror Info & Install Modal
# -----------------------------------------------------------------
class ScrcpyModal(ModalScreen[None]):
    """Modal displaying instructions on how to install and configure scrcpy for screen mirroring."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("scrcpy_modal_title"), classes="modal-title")
            yield Static(t("scrcpy_modal_desc"), classes="modal-subtitle")
            yield Static(
                f"[bold #73daca]{t('scrcpy_install_guide')}[/]",
                classes="modal-subtitle",
            )
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_close"), id="btn-close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


# -----------------------------------------------------------------
# 13. Column Widths Adjustment Modal
# -----------------------------------------------------------------
class ColumnWidthsModal(ModalScreen[Optional[dict]]):
    """
    Modal allowing the user to customize column widths for Name, Size, Type,
    Modified date, and Permissions, or choose between Compact, Standard, and Expanded presets.
    """

    def __init__(self, current_widths: dict, **kwargs):
        super().__init__(**kwargs)
        self.widths = dict(current_widths)

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("col_widths_title"), classes="modal-title")
            yield Static(t("col_widths_desc"), classes="modal-subtitle")

            # Presets
            with Horizontal(classes="button-bar", id="preset-bar"):
                yield Button(f"📱 {t('preset_compact')}", id="btn-preset-compact")
                yield Button(f"⚖️ {t('preset_standard')}", id="btn-preset-standard", variant="primary")
                yield Button(f"🖥️ {t('preset_expanded')}", id="btn-preset-expanded")

            col_specs = [
                ("name", t("col_w_name")),
                ("size", t("col_w_size")),
                ("type", t("col_w_type")),
                ("modified", t("col_w_mod")),
                ("perms", t("col_w_perms")),
            ]
            for col_id, col_name in col_specs:
                with Horizontal(classes="width-adjust-row"):
                    yield Static(f"{col_name}:", classes="col-adjust-label")
                    yield Button("➖", id=f"btn-dec-{col_id}", classes="btn-adjust")
                    yield Static(f"{self.widths.get(col_id, 20)}", id=f"val-{col_id}", classes="col-adjust-val")
                    yield Button("➕", id=f"btn-inc-{col_id}", classes="btn-adjust")

            with Horizontal(classes="button-bar"):
                yield Button(t("btn_apply"), id="btn-apply", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def _update_display(self) -> None:
        for col_id in ["name", "size", "type", "modified", "perms"]:
            val_widget = self.query_one(f"#val-{col_id}", Static)
            val_widget.update(str(self.widths.get(col_id, 20)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-preset-compact":
            self.widths = {"sel": 5, "name": 24, "size": 10, "type": 10, "modified": 16, "perms": 10}
            self._update_display()
        elif btn_id == "btn-preset-standard":
            self.widths = {"sel": 5, "name": 34, "size": 12, "type": 12, "modified": 18, "perms": 12}
            self._update_display()
        elif btn_id == "btn-preset-expanded":
            self.widths = {"sel": 5, "name": 48, "size": 14, "type": 14, "modified": 22, "perms": 14}
            self._update_display()
        elif btn_id and btn_id.startswith("btn-dec-"):
            col = btn_id.replace("btn-dec-", "")
            self.widths[col] = max(6, self.widths.get(col, 20) - 2)
            self._update_display()
        elif btn_id and btn_id.startswith("btn-inc-"):
            col = btn_id.replace("btn-inc-", "")
            self.widths[col] = min(80, self.widths.get(col, 20) + 2)
            self._update_display()
        elif btn_id == "btn-apply":
            self.dismiss(self.widths)
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 14. Sort Selection Modal
# -----------------------------------------------------------------
class SortModal(ModalScreen[Optional[str]]):
    """Modal allowing the user to pick sorting criterion (Name, Size, Type, Date, Perms) and invert order."""

    def __init__(self, current_sort: str = "name", is_reverse: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.current_sort = current_sort
        self.is_reverse = is_reverse

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static(t("sort_modal_title"), classes="modal-title")
            order_name = t("order_desc") if self.is_reverse else t("order_asc")
            yield Static(
                t("sort_modal_subtitle", sort=self.current_sort.upper(), order=order_name),
                classes="modal-subtitle",
            )
            with Vertical(classes="dialog-options-col"):
                yield Button(t("sort_btn_name"), id="btn-sort-name", classes="btn-dialog-choice")
                yield Button(t("sort_btn_size"), id="btn-sort-size", classes="btn-dialog-choice")
                yield Button(t("sort_btn_type"), id="btn-sort-type", classes="btn-dialog-choice")
                yield Button(t("sort_btn_modified"), id="btn-sort-modified", classes="btn-dialog-choice")
                yield Button(t("sort_btn_perms"), id="btn-sort-perms", classes="btn-dialog-choice")
                yield Button(t("sort_btn_invert", order=order_name), id="btn-sort-invert", classes="btn-dialog-choice", variant="primary")

            with Horizontal(classes="button-bar"):
                yield Button(t("btn_close"), id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-sort-name":
            self.dismiss("name")
        elif btn_id == "btn-sort-size":
            self.dismiss("size")
        elif btn_id == "btn-sort-type":
            self.dismiss("type")
        elif btn_id == "btn-sort-modified":
            self.dismiss("modified")
        elif btn_id == "btn-sort-perms":
            self.dismiss("perms")
        elif btn_id == "btn-sort-invert":
            self.dismiss("invert")
        else:
            self.dismiss(None)

