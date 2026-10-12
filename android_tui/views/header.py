"""
Header component for AndroidTUI.
Displays app branding, device connection status, connection stability/latency,
battery, storage, and active path with mouse click support.
"""
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static
from typing import Optional

from ..models import AdbDevice, ConnectionType, DeviceState


class HeaderBar(Static):
    """Top bar displaying device information, connection stability, battery, and breadcrumb path."""

    def __init__(self, **kwargs):
        super().__init__(id="header-bar", **kwargs)
        self.device: Optional[AdbDevice] = None
        self.current_path: str = "/sdcard"
        self.latency_ms: Optional[int] = None
        self.is_alive: bool = False

    def compose(self) -> ComposeResult:
        yield Static("⚡ AndroidTUI", id="header-logo")
        yield Static(" [Non Connesso] ", id="header-device-badge")
        yield Static("", id="header-stats")
        yield Static("📱 /sdcard", id="header-path")

    def update_state(self, device: Optional[AdbDevice], current_path: str) -> None:
        self.device = device
        self.current_path = current_path

        badge_widget = self.query_one("#header-device-badge", Static)
        stats_widget = self.query_one("#header-stats", Static)
        path_widget = self.query_one("#header-path", Static)

        if not device or device.state != DeviceState.DEVICE:
            badge_widget.update(" ⚠️ Disconnesso ")
            badge_widget.styles.color = "#f7768e"
            badge_widget.styles.background = "#2d1c24"
            stats_widget.update("Nessun dispositivo pronto · Clicca qui per collegare")
            path_widget.update("")
            return

        # Device is connected
        conn_icon = "🔌 USB" if device.connection_type == ConnectionType.USB else (
            "📶 WiFi" if device.connection_type == ConnectionType.WIRELESS else "🎮 Demo"
        )
        badge_text = f" {conn_icon} : {device.display_name} "
        badge_widget.update(badge_text)
        badge_widget.styles.color = "#73daca"
        badge_widget.styles.background = "#1f332c"

        stats_parts = []
        if self.latency_ms is not None and self.is_alive:
            if self.latency_ms < 80:
                stats_parts.append(f"🟢 {self.latency_ms}ms (Ottima)")
            elif self.latency_ms < 200:
                stats_parts.append(f"🟡 {self.latency_ms}ms (Buona)")
            else:
                stats_parts.append(f"🟠 {self.latency_ms}ms (Lenta)")
        elif not self.is_alive and self.device:
            stats_parts.append("🔴 Segnale perso")

        if device.android_version:
            stats_parts.append(f"Android {device.android_version}")
        if device.battery_level is not None:
            stats_parts.append(f"🔋 {device.battery_level}%")
        if device.storage_free:
            stats_parts.append(f"💾 Libero: {device.storage_free}")

        stats_widget.update(" · ".join(stats_parts))
        path_widget.update(f"📱 {current_path}")

    def update_stability(self, latency_ms: Optional[int], is_alive: bool) -> None:
        self.latency_ms = latency_ms
        self.is_alive = is_alive
        if self.device and self.device.state == DeviceState.DEVICE:
            self.update_state(self.device, self.current_path)

    def on_click(self, event) -> None:
        widget = event.widget
        if widget and widget.id == "header-device-badge":
            self.app.action_manage_devices()
        elif widget and widget.id == "header-path":
            self.app.action_go_parent()
        elif widget and widget.id == "header-logo":
            self.app.action_show_help()
        elif widget and widget.id == "header-stats":
            self.app.check_connection_stability()

