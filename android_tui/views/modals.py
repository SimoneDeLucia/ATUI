"""
Interactive Modals and Dialogs for AndroidTUI.
Provides popups for Wireless Pairing/Connect, Device Selection & Addition,
Download/Upload transfers, File management (rename/delete/new folder),
Path Breadcrumbs navigation, Settings and Keyboard shortcuts Help.
"""
import os
from pathlib import Path
from typing import List, Optional, Tuple, Any, Dict
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
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
            yield Static("📶 Connessione Debug Wireless", classes="modal-title")
            yield Static(
                "Inserisci l'indirizzo IP e la porta visualizzati sul telefono in\n"
                "[bold]Opzioni Sviluppatore > Debug Wireless[/] (es. 192.168.1.50:5555):",
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
            yield Static("📶 Accoppiamento Wireless (Pairing)", classes="modal-title")
            yield Static(
                "In [bold]Debug Wireless > Accoppia dispositivo con codice[/]:\n"
                "1. Inserisci IP e Porta di accoppiamento\n"
                "2. Inserisci il codice a 6 cifre visualizzato sullo schermo",
                classes="modal-subtitle",
            )
            yield Static("Indirizzo IP e Porta (es. 192.168.1.50:37123):")
            yield Input(placeholder="192.168.1.x:porta", id="input-pair-addr")
            yield Static("Codice di accoppiamento a 6 cifre:")
            yield Input(placeholder="es. 123456", id="input-pair-code")
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
            yield Static("⚠️ Conferma Eliminazione Multipla (Batch)", classes="modal-title")
            names_preview = ", ".join(e.name for e in self.entries[:4])
            if len(self.entries) > 4:
                names_preview += f" ... e altri {len(self.entries) - 4} file"
            yield Static(
                f"Sei sicuro di voler eliminare definitivamente [bold #f7768e]{len(self.entries)} elementi[/] dal telefono?\n\n"
                f"[dim]Elementi: {names_preview}[/]\n\n"
                f"[bold #f7768e]Questa operazione è irreversibile e cancellerà i file selezionati.[/]",
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
                "$f.Description = 'Seleziona la cartella di destinazione per salvare i file'; "
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


class DownloadModal(ModalScreen[Optional[str]]):
    """Modal to download selected file or folder from Phone to PC."""

    def __init__(self, remote_name: str, remote_path: str, default_pc_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.remote_name = remote_name
        self.remote_path = remote_path
        self.default_pc_dir = default_pc_dir

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static("📥 Scarica su PC (adb pull)", classes="modal-title")
            yield Static(
                f"Elemento da scaricare dal telefono:\n[bold #7dcfff]{self.remote_path}[/]\n\n"
                f"Cartella di destinazione sul tuo PC:",
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
            yield Static("📥 Download Batch Multi-File (adb pull)", classes="modal-title")
            total_bytes = sum(e.size for e in self.entries if not e.is_dir)
            total_str = self._format_size(total_bytes)
            names_preview = ", ".join(e.name for e in self.entries[:4])
            if len(self.entries) > 4:
                names_preview += f" ... e altri {len(self.entries) - 4} file"

            yield Static(
                f"Elementi selezionati per il download:\n"
                f"[bold #7dcfff]{len(self.entries)} elementi[/] (totale: [bold #73daca]{total_str}[/])\n"
                f"[dim]File: {names_preview}[/]\n\n"
                f"Cartella di destinazione sul PC:",
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
            summary_txt = f"{len(self.entries)} elementi" if len(self.entries) > 1 else (self.entries[0].name if self.entries else "")
            yield Static(f"[dim]Oggetto del trasferimento: [bold #7dcfff]{summary_txt}[/][/]", classes="modal-subtitle")

            # Selection buttons between PC and Android
            with Horizontal(classes="button-bar", id="d2d-choice-bar"):
                yield Button(t("transfer_mode_pc"), id="btn-choice-pc", variant="primary")
                has_devs = bool(self.other_devices)
                dev_btn_lbl = t("transfer_mode_device")
                if not has_devs:
                    dev_btn_lbl += " (Nessun 2° dispositivo)"
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
class UploadModal(ModalScreen[Optional[str]]):
    """Modal to upload local file from PC to Phone."""

    def __init__(self, current_phone_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.current_phone_dir = current_phone_dir

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static("📤 Carica File su Telefono (adb push)", classes="modal-title")
            yield Static(
                f"Cartella di destinazione sul telefono:\n[bold #7dcfff]{self.current_phone_dir}[/]\n\n"
                f"Inserisci il percorso del file o cartella locale sul PC:",
                classes="modal-subtitle",
            )
            yield Input(placeholder=r"C:\Users\...\file.apk", id="input-pc-src")
            with Horizontal(classes="button-bar"):
                yield Button(t("btn_upload_now"), id="btn-submit", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit":
            val = self.query_one("#input-pc-src", Input).value.strip()
            self.dismiss(val if val else None)
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 6. Create Folder Modal
# -----------------------------------------------------------------
class CreateFolderModal(ModalScreen[Optional[str]]):
    """Modal to create a new folder on Phone."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static("📁 Nuova Cartella", classes="modal-title")
            yield Static("Inserisci il nome della nuova cartella sul telefono:", classes="modal-subtitle")
            yield Input(placeholder="Nome cartella", id="input-folder-name")
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
            yield Static("✏️ Rinomina Elemento", classes="modal-title")
            yield Static(f"Modifica il nome per [bold #7dcfff]{self.current_name}[/]:", classes="modal-subtitle")
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
            yield Static("⚠️ Conferma Eliminazione", classes="modal-title")
            kind = "la cartella e tutto il suo contenuto" if self.is_dir else "il file"
            yield Static(
                f"Sei sicuro di voler eliminare definitivamente {kind}?\n\n"
                f"[bold #f7768e]{self.target_path}[/]\n\n"
                f"[dim]Questa operazione non può essere annullata.[/]",
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
    """Modal showing all keyboard shortcuts and ADB tips."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static("📖 Guida & Scorciatoie da Tastiera — AndroidTUI", classes="modal-title")
            help_content = (
                "[bold #7dcfff]Navigazione File System:[/\n]"
                "  • [bold #73daca]↑ / k[/]         Sposta cursore in alto\n"
                "  • [bold #73daca]↓ / j[/]         Sposta cursore in basso\n"
                "  • [bold #73daca]Enter / l[/]     Apri cartella selezionata\n"
                "  • [bold #73daca]Backspace / h[/] Torna alla cartella genitore\n"
                "  • [bold #73daca]p[/]             Seleziona cartella o sottocartella nel percorso (Breadcrumbs)\n"
                "  • [bold #73daca]s / S[/]         Ordina per Nome, Dimensione o Tipo (Inverti ordine)\n"
                "  • [bold #73daca]m[/]             Condivisione schermo in tempo reale con Scrcpy\n\n"
                "[bold #7dcfff]Selezione Multipla & Batch:[/\n]"
                "  • [bold #73daca]Spazio (Space)[/]  Seleziona/deseleziona file (mantiene il cursore)\n"
                "  • [bold #73daca]a[/]             Seleziona / deseleziona tutti i file\n\n"
                "[bold #7dcfff]Gestione File & Trasferimenti:[/\n]"
                "  • [bold #73daca]d[/]             [bold]Scarica su PC (adb pull)[/] (singolo o batch)\n"
                "  • [bold #73daca]u[/]             [bold]Carica dal PC al telefono (adb push)[/]\n"
                "  • [bold #73daca]f[/]             Crea nuova cartella (mkdir)\n"
                "  • [bold #73daca]n[/]             Rinomina elemento (mv)\n"
                "  • [bold #73daca]x[/]             Elimina elemento (rm -rf)\n"
                "  • [bold #73daca]r[/]             Ricarica la cartella corrente\n\n"
                "[bold #7dcfff]Interazione con Mouse:[/\n]"
                "  • Clicca sui quadrati [✓] / [ ] per selezionare i file con il mouse\n"
                "  • Clicca sulle intestazioni colonna (Nome, Dimensione, Tipo) per ordinare\n"
                "  • Clicca sul percorso in alto per saltare alle sottocartelle\n"
                "  • Clicca sui pulsanti in basso nel footer per eseguire le azioni\n\n"
                "[bold #7dcfff]Connessioni & Dispositivi:[/\n]"
                "  • [bold #73daca]c[/]             Menu gestione e aggiunta dispositivi (USB & Wireless)\n"
                "  • [bold #73daca]F2[/]            Cambia lingua (Italiano / English)\n"
                "  • [bold #73daca]?[/]             Mostra questa schermata di aiuto\n"
                "  • [bold #73daca]q[/]             Esci da AndroidTUI\n"
            )
            yield Static(help_content, classes="modal-subtitle")
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

        is_it = (get_current_language() == "it")

        # 1. Internal Storage
        int_free = f" ({device.storage_free} lib.)" if device and device.storage_free else ""
        int_lbl = f"Memoria Interna: /sdcard{int_free}" if is_it else f"Internal Storage: /sdcard{int_free}"
        self.locations.append((int_lbl, "/sdcard", "📱"))

        # 2. External MicroSD (Only present if device has an external MicroSD!)
        if device and device.ext_sd_path:
            sd_free = f" ({device.ext_sd_free} lib.)" if device.ext_sd_free else ""
            sd_lbl = f"MicroSD: {device.ext_sd_path}{sd_free}"
            self.locations.append((sd_lbl, device.ext_sd_path, "💾"))

        # 3. Downloads
        self.locations.append(("Downloads: /sdcard/Download", "/sdcard/Download", "📥"))

        # 4. Photos / Camera (DCIM)
        dcim_lbl = "DCIM (Fotocamera): /sdcard/DCIM" if is_it else "DCIM (Camera): /sdcard/DCIM"
        self.locations.append((dcim_lbl, "/sdcard/DCIM", "📷"))

        # 5. Pictures
        self.locations.append(("Pictures: /sdcard/Pictures", "/sdcard/Pictures", "🖼️"))

        # 6. System Root
        root_lbl = "Root di Sistema: /" if is_it else "System Root: /"
        self.locations.append((root_lbl, "/", "⚙️"))

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
                        curr_tag = " [Cartella Attuale]" if get_current_language() == "it" else " [Current Folder]"
                        t_lbl.append(curr_tag, style="dim #73daca")
                    else:
                        t_lbl.append("📁 ", style="bold #7dcfff")
                        t_lbl.append(label, style="bold #c0caf5")
                    yield ListItem(Label(t_lbl), id=f"bc-item-{idx}")

            # Quick Folders Jump Section (Download, sdcard, MicroSD, DCIM, Video)
            yield Static(f"[bold #7dcfff]{t('breadcrumb_quick_locations')}[/]", classes="meta-key")
            with Horizontal(classes="quick-folders-bar", id="quick-folders-bar"):
                yield Button("📥 Download", id="qf-download")
                yield Button("📱 sdcard", id="qf-sdcard")
                if self.device and self.device.ext_sd_path:
                    yield Button("💾 MicroSD", id="qf-microsd")
                yield Button("📷 DCIM", id="qf-dcim")
                yield Button("🎬 Video", id="qf-video")

            yield Static(f"[bold #7dcfff]{t('breadcrumb_input_placeholder')}:[/]", classes="meta-key")
            yield Input(value=self.current_path, id="input-custom-path", placeholder="/sdcard/...")

            with Horizontal(classes="button-bar"):
                yield Button(t("breadcrumb_btn_go"), id="btn-go", variant="primary")
                yield Button(t("btn_cancel"), id="btn-cancel")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.segments):
            _, target_path = self.segments[idx]
            self.dismiss(target_path)

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
            list_view = self.query_one("#breadcrumb-list", ListView)
            idx = list_view.index
            if idx is not None and 0 <= idx < len(self.segments):
                _, target_path = self.segments[idx]
                self.dismiss(target_path)
            else:
                self.dismiss(input_val if input_val else None)
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
            yield Static("🔄 Ordinamento File e Cartelle", classes="modal-title")
            order_name = t("order_desc") if self.is_reverse else t("order_asc")
            yield Static(
                f"Ordinamento attuale: [bold #7dcfff]{self.current_sort.upper()}[/] ({order_name})\n"
                f"Scegli il criterio per ordinare i file nella tabella:",
                classes="modal-subtitle",
            )
            with Vertical(classes="dialog-options-col"):
                yield Button("🔤 Ordina per Nome", id="btn-sort-name", classes="btn-dialog-choice")
                yield Button("⚖️ Ordina per Dimensione", id="btn-sort-size", classes="btn-dialog-choice")
                yield Button("📁 Ordina per Tipo di File", id="btn-sort-type", classes="btn-dialog-choice")
                yield Button("🕒 Ordina per Data di Modifica", id="btn-sort-modified", classes="btn-dialog-choice")
                yield Button("🔒 Ordina per Permessi", id="btn-sort-perms", classes="btn-dialog-choice")
                yield Button(f"🔄 Inverti Direzione (Attuale: {order_name})", id="btn-sort-invert", classes="btn-dialog-choice", variant="primary")

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

