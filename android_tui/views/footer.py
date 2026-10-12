"""
Footer component for AndroidTUI.
Displays interactive clickable action buttons for mouse interaction,
batch selection badge, and real-time status toasts with i18n support.
"""
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Button, ProgressBar

from ..i18n import t


class FooterBar(Static):
    """Interactive bottom bar with clickable action buttons, live progress bar, and status toasts."""

    def __init__(self, **kwargs):
        super().__init__(id="footer-bar", **kwargs)
        self._current_toast = t("ready")
        self._batch_count = 0
        self._batch_size_str = ""

    def compose(self) -> ComposeResult:
        with Horizontal(id="footer-buttons-row"):
            yield Button(t("fbtn_enter"), id="fbtn-enter", classes="footer-pill")
            yield Button(t("fbtn_select"), id="fbtn-select", classes="footer-pill")
            yield Button(t("fbtn_download"), id="fbtn-download", classes="footer-pill")
            yield Button(t("fbtn_upload"), id="fbtn-upload", classes="footer-pill")
            yield Button(t("fbtn_mkdir"), id="fbtn-mkdir", classes="footer-pill")
            yield Button(t("fbtn_rename"), id="fbtn-rename", classes="footer-pill")
            yield Button(t("fbtn_delete"), id="fbtn-delete", classes="footer-pill")
            yield Button(t("fbtn_devices"), id="fbtn-devices", classes="footer-pill")
            yield Button(t("fbtn_disconnect"), id="fbtn-disconnect", classes="footer-pill")
            yield Button(t("fbtn_refresh"), id="fbtn-refresh", classes="footer-pill")
            yield Button(t("fbtn_help"), id="fbtn-help", classes="footer-pill")
            yield Button(t("fbtn_quit"), id="fbtn-quit", classes="footer-pill")

        with Horizontal(id="footer-status-row"):
            yield Static("", id="footer-batch-badge")
            with Horizontal(id="footer-batch-actions"):
                yield Button(t("fbtn_batch_dl", count=0), id="fbtn-batch-download", classes="batch-pill-download")
                yield Button(t("fbtn_batch_del", count=0), id="fbtn-batch-delete", classes="batch-pill-delete")
                yield Button(t("fbtn_batch_clear"), id="fbtn-batch-clear", classes="batch-pill-clear")
            yield ProgressBar(id="footer-progress", show_percentage=True, show_eta=False)
            yield Static(self._current_toast, id="footer-toast")

    def update_texts(self) -> None:
        """Refreshes localized button labels in the footer."""
        buttons_map = {
            "#fbtn-enter": "fbtn_enter",
            "#fbtn-select": "fbtn_select",
            "#fbtn-download": "fbtn_download",
            "#fbtn-upload": "fbtn_upload",
            "#fbtn-mkdir": "fbtn_mkdir",
            "#fbtn-rename": "fbtn_rename",
            "#fbtn-delete": "fbtn_delete",
            "#fbtn-devices": "fbtn_devices",
            "#fbtn-disconnect": "fbtn_disconnect",
            "#fbtn-refresh": "fbtn_refresh",
            "#fbtn-help": "fbtn_help",
            "#fbtn-quit": "fbtn_quit",
            "#fbtn-batch-clear": "fbtn_batch_clear",
        }
        for sel, key in buttons_map.items():
            btn = self.query_one(sel, Button)
            btn.label = t(key)

        self.update_batch_selection(self._batch_count, self._batch_size_str)

    def show_toast(self, message: str, is_error: bool = False) -> None:
        self._current_toast = message
        toast_widget = self.query_one("#footer-toast", Static)
        if is_error:
            toast_widget.update(f"❌ {message}")
            toast_widget.styles.color = "#f7768e"
        else:
            toast_widget.update(f"✓ {message}")
            toast_widget.styles.color = "#73daca"

    def update_batch_selection(self, count: int, total_size_str: str) -> None:
        self._batch_count = count
        self._batch_size_str = total_size_str

        badge = self.query_one("#footer-batch-badge", Static)
        batch_actions = self.query_one("#footer-batch-actions", Horizontal)
        btn_dl = self.query_one("#fbtn-batch-download", Button)
        btn_del = self.query_one("#fbtn-batch-delete", Button)

        if count > 0:
            badge.update(t("batch_badge", count=count, size=total_size_str))
            badge.styles.display = "block"
            btn_dl.label = t("fbtn_batch_dl", count=count)
            btn_del.label = t("fbtn_batch_del", count=count)
            batch_actions.styles.display = "block"
        else:
            badge.update("")
            badge.styles.display = "none"
            batch_actions.styles.display = "none"

    def start_progress(self, total: float = 100, label: str = "") -> None:
        """Displays and initializes the footer progress bar for file transfer operations."""
        prog = self.query_one("#footer-progress", ProgressBar)
        prog.update(total=total, progress=0)
        prog.styles.display = "block"
        if label:
            self.show_toast(label)

    def update_progress(self, advance: float = 1, current: Optional[float] = None) -> None:
        """Advances or updates the footer progress bar value."""
        prog = self.query_one("#footer-progress", ProgressBar)
        if current is not None:
            prog.update(progress=current)
        else:
            prog.advance(advance)

    def finish_progress(self) -> None:
        """Hides the footer progress bar once file transfer completes."""
        prog = self.query_one("#footer-progress", ProgressBar)
        prog.styles.display = "none"

