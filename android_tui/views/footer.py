"""
Footer component for AndroidTUI.
Displays interactive clickable action buttons for mouse interaction,
batch selection badge, and real-time status toasts.
"""
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Button


class FooterBar(Static):
    """Interactive bottom bar with clickable action buttons and live status toasts."""

    def __init__(self, **kwargs):
        super().__init__(id="footer-bar", **kwargs)
        self._current_toast = "Pronto."

    def compose(self) -> ComposeResult:
        with Horizontal(id="footer-buttons-row"):
            yield Button("⏎ Apri", id="fbtn-enter", classes="footer-pill")
            yield Button("␣ Seleziona", id="fbtn-select", classes="footer-pill")
            yield Button("📥 Scarica", id="fbtn-download", classes="footer-pill")
            yield Button("📤 Carica", id="fbtn-upload", classes="footer-pill")
            yield Button("📁 Cartella", id="fbtn-mkdir", classes="footer-pill")
            yield Button("✏️ Rinomina", id="fbtn-rename", classes="footer-pill")
            yield Button("🗑️ Elimina", id="fbtn-delete", classes="footer-pill")
            yield Button("📱 Dispositivi", id="fbtn-devices", classes="footer-pill")
            yield Button("🔄 Ricarica", id="fbtn-refresh", classes="footer-pill")
            yield Button("❓ Aiuto", id="fbtn-help", classes="footer-pill")
            yield Button("✕ Esci", id="fbtn-quit", classes="footer-pill")

        with Horizontal(id="footer-status-row"):
            yield Static("", id="footer-batch-badge")
            yield Static(self._current_toast, id="footer-toast")

    def show_toast(self, message: str, is_error: bool = False) -> None:
        toast_widget = self.query_one("#footer-toast", Static)
        if is_error:
            toast_widget.update(f"❌ {message}")
            toast_widget.styles.color = "#f7768e"
        else:
            toast_widget.update(f"✓ {message}")
            toast_widget.styles.color = "#73daca"

    def update_batch_selection(self, count: int, total_size_str: str) -> None:
        badge = self.query_one("#footer-batch-badge", Static)
        if count > 0:
            badge.update(f" 🧺 {count} selezionati ({total_size_str}) ")
            badge.styles.display = "block"
        else:
            badge.update("")
            badge.styles.display = "none"
