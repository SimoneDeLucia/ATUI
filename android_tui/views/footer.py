"""
Footer component for AndroidTUI.
Displays keyboard shortcuts pill bar and real-time status toasts.
"""
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class FooterBar(Static):
    """Bottom bar displaying keyboard shortcuts and operational toast messages."""

    def __init__(self, **kwargs):
        super().__init__(id="footer-bar", **kwargs)
        self._current_toast = "Pronto."

    def compose(self) -> ComposeResult:
        # PikPakTUI style keyboard shortcuts
        keys_markup = (
            "[bold #7dcfff]\\[Enter][/] Apri  "
            "[bold #7dcfff]\\[d][/] Scarica su PC  "
            "[bold #7dcfff]\\[u][/] Carica su Tel  "
            "[bold #7dcfff]\\[f][/] Nuova Cartella  "
            "[bold #7dcfff]\\[n][/] Rinomina  "
            "[bold #7dcfff]\\[x][/] Elimina  "
            "[bold #7dcfff]\\[c][/] Dispositivi  "
            "[bold #7dcfff]\\[r][/] Ricarica  "
            "[bold #7dcfff]\\[?][/] Aiuto  "
            "[bold #7dcfff]\\[q][/] Esci"
        )
        yield Static(keys_markup, id="footer-keys")
        yield Static(self._current_toast, id="footer-toast")

    def show_toast(self, message: str, is_error: bool = False) -> None:
        toast_widget = self.query_one("#footer-toast", Static)
        if is_error:
            toast_widget.update(f"❌ {message}")
            toast_widget.styles.color = "#f7768e"
        else:
            toast_widget.update(f"✓ {message}")
            toast_widget.styles.color = "#73daca"
