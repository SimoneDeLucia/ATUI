"""
Header component for AndroidTUI.
Displays app branding, device connection status, battery, storage, and active path.
"""
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static
from typing import Optional

from ..models import AdbDevice, ConnectionType, DeviceState


class HeaderBar(Static):
    """Top bar displaying device information, connection type, battery, and breadcrumb path."""

    def __init__(self, **kwargs):
        super().__init__(id="header-bar", **kwargs)
        self.device: Optional[AdbDevice] = None
        self.current_path: str = "/sdcard"

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
            stats_widget.update("Nessun dispositivo pronto · Premi [c] per collegare")
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
        if device.android_version:
            stats_parts.append(f"Android {device.android_version}")
        if device.battery_level is not None:
            stats_parts.append(f"🔋 {device.battery_level}%")
        if device.storage_free:
            stats_parts.append(f"💾 Libero: {device.storage_free}")

        stats_widget.update(" · ".join(stats_parts))
        path_widget.update(f"📱 {current_path}")
