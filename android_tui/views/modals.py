"""
Interactive Modals and Dialogs for AndroidTUI.
Provides popups for Wireless Pairing/Connect, Device Selection,
Download/Upload transfers, File management (rename/delete/new folder),
Settings and Keyboard shortcuts Help.
"""
import os
from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Static, Input, Button, ListView, ListItem, Label
from rich.text import Text

from ..models import AdbDevice, ConnectionType, DeviceState


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
                yield Button("Connetti", id="btn-submit", variant="primary")
                yield Button("Annulla", id="btn-cancel")

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
                yield Button("Accoppia", id="btn-submit", variant="primary")
                yield Button("Annulla", id="btn-cancel")

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
# 3. Device Selection Modal
# -----------------------------------------------------------------
class DeviceSelectModal(ModalScreen[Optional[AdbDevice]]):
    """Modal to select active device among connected USB / Wireless devices."""

    def __init__(self, devices: List[AdbDevice], **kwargs):
        super().__init__(**kwargs)
        self.devices = devices

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Static("📱 Seleziona Dispositivo Android", classes="modal-title")
            yield Static("Elenco dei dispositivi rilevati dal server ADB:", classes="modal-subtitle")
            
            with ListView(id="device-list"):
                for dev in self.devices:
                    icon = "🔌" if dev.connection_type == ConnectionType.USB else (
                        "📶" if dev.connection_type == ConnectionType.WIRELESS else "🎮"
                    )
                    state_color = "#73daca" if dev.state == DeviceState.DEVICE else "#f7768e"
                    t = Text()
                    t.append(f"{icon} {dev.display_name} ", style="bold #c0caf5")
                    t.append(f"({dev.serial}) ", style="dim")
                    t.append(f"[{dev.state.value.upper()}]", style=f"bold {state_color}")
                    yield ListItem(Label(t), id=f"dev-{dev.serial}")

            with Horizontal(classes="button-bar"):
                yield Button("Seleziona", id="btn-select", variant="primary")
                yield Button("Chiudi", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-select":
            list_view = self.query_one("#device-list", ListView)
            if list_view.highlighted_child:
                idx = list_view.index
                if idx is not None and 0 <= idx < len(self.devices):
                    self.dismiss(self.devices[idx])
                    return
            self.dismiss(None)
        else:
            self.dismiss(None)


# -----------------------------------------------------------------
# 4. Download / Pull Modal
# -----------------------------------------------------------------
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
            yield Input(value=self.default_pc_dir, id="input-pc-dest")
            with Horizontal(classes="button-bar"):
                yield Button("Scarica Ora", id="btn-submit", variant="primary")
                yield Button("Annulla", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit":
            val = self.query_one("#input-pc-dest", Input).value.strip()
            self.dismiss(val if val else None)
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
            yield Input(placeholder=r"C:\Users\SiMonee\Downloads\documento.pdf", id="input-pc-src")
            with Horizontal(classes="button-bar"):
                yield Button("Carica Ora", id="btn-submit", variant="primary")
                yield Button("Annulla", id="btn-cancel")

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
                yield Button("Crea", id="btn-submit", variant="primary")
                yield Button("Annulla", id="btn-cancel")

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
                yield Button("Rinomina", id="btn-submit", variant="primary")
                yield Button("Annulla", id="btn-cancel")

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
                yield Button("Elimina Definitivamente", id="btn-delete", variant="error")
                yield Button("Annulla", id="btn-cancel")

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
                "  • [bold #73daca]↑ / k[/]       Sposta cursore in alto\n"
                "  • [bold #73daca]↓ / j[/]       Sposta cursore in basso\n"
                "  • [bold #73daca]Enter / l[/]   Apri cartella selezionata\n"
                "  • [bold #73daca]Backspace / h[/] Torna alla cartella superiore (genitore)\n\n"
                "[bold #7dcfff]Gestione File & Trasferimenti:[/\n]"
                "  • [bold #73daca]d[/]           [bold]Scarica su PC (adb pull)[/]\n"
                "  • [bold #73daca]u[/]           [bold]Carica dal PC al telefono (adb push)[/]\n"
                "  • [bold #73daca]f[/]           Crea nuova cartella (mkdir)\n"
                "  • [bold #73daca]n[/]           Rinomina elemento (mv)\n"
                "  • [bold #73daca]x[/]           Elimina elemento (rm -rf)\n"
                "  • [bold #73daca]r[/]           Ricarica la cartella corrente\n\n"
                "[bold #7dcfff]Connessioni & Dispositivi:[/\n]"
                "  • [bold #73daca]c[/]           Menu gestione dispositivi (USB & Wireless)\n"
                "  • [bold #73daca]?[/]           Mostra questa schermata di aiuto\n"
                "  • [bold #73daca]q[/]           Esci da AndroidTUI\n"
            )
            yield Static(help_content, classes="modal-subtitle")
            with Horizontal(classes="button-bar"):
                yield Button("Chiudi", id="btn-close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)
