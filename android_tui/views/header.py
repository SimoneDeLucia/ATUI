"""
Header component for AndroidTUI.
Displays app branding, device connection status, connection stability/latency,
battery, known storage locations (Internal / MicroSD), active path, and language toggle.
"""
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static, Button

from ..models import AdbDevice, ConnectionType, DeviceState
from ..i18n import t, get_current_language


class HeaderBar(Static):
    """Top bar displaying device info, stability, storage locations, and breadcrumbs."""

    def __init__(self, **kwargs):
        super().__init__(id="header-bar", **kwargs)
        self.device: Optional[AdbDevice] = None
        self.current_path: str = "/sdcard"
        self.latency_ms: Optional[int] = None
        self.is_alive: bool = False

    def compose(self) -> ComposeResult:
        yield Static("⚡ AndroidTUI", id="header-logo")
        yield Static(t("header_disconnected"), id="header-device-badge")
        yield Static("", id="header-stats")
        yield Static("📱 /sdcard", id="header-path")
        with Horizontal(id="header-actions"):
            yield Button("🖥️ Scrcpy", id="hbtn-scrcpy", classes="header-btn")
            yield Button("📱 Interna", id="hbtn-sdcard", classes="header-btn")
            yield Button("💾 MicroSD", id="hbtn-extsd", classes="header-btn")
            yield Button("🌐 IT", id="hbtn-lang", classes="header-btn")

    def update_texts(self) -> None:
        """Refreshes localized labels in the header."""
        self.update_state(self.device, self.current_path)

    def update_state(self, device: Optional[AdbDevice], current_path: str) -> None:
        self.device = device
        self.current_path = current_path

        badge_widget = self.query_one("#header-device-badge", Static)
        stats_widget = self.query_one("#header-stats", Static)
        path_widget = self.query_one("#header-path", Static)
        btn_scrcpy = self.query_one("#hbtn-scrcpy", Button)
        btn_sdcard = self.query_one("#hbtn-sdcard", Button)
        btn_extsd = self.query_one("#hbtn-extsd", Button)
        btn_lang = self.query_one("#hbtn-lang", Button)

        btn_scrcpy.label = t("scrcpy_btn")
        btn_lang.label = f"🌐 {get_current_language().upper()}"
        btn_sdcard.label = t("header_internal")
        btn_extsd.label = t("header_sd")

        if not device or device.state != DeviceState.DEVICE:
            badge_widget.update(t("header_disconnected"))
            badge_widget.styles.color = "#f7768e"
            badge_widget.styles.background = "#2d1c24"
            stats_widget.update(t("header_no_device_ready"))
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
                stats_parts.append(f"🟢 {self.latency_ms}ms ({t('header_latency_excellent')})")
            elif self.latency_ms < 200:
                stats_parts.append(f"🟡 {self.latency_ms}ms ({t('header_latency_good')})")
            else:
                stats_parts.append(f"🟠 {self.latency_ms}ms ({t('header_latency_slow')})")
        elif not self.is_alive and self.device:
            stats_parts.append(t("header_signal_lost"))

        if device.android_version:
            stats_parts.append(f"Android {device.android_version}")
        if device.battery_level is not None:
            stats_parts.append(f"🔋 {device.battery_level}%")

        # Internal storage
        if device.storage_free:
            stats_parts.append(f"{t('header_internal')}: {device.storage_free} {t('header_free')}")

        # External MicroSD
        if device.ext_sd_path:
            stats_parts.append(f"{t('header_sd')}: {device.ext_sd_free or 'OK'} {t('header_free')}")
        else:
            stats_parts.append(f"{t('header_sd')}: {t('header_no_sd')}")

        stats_widget.update(" · ".join(stats_parts))
        path_widget.update(f"📂 {current_path}")

    def update_stability(self, latency_ms: Optional[int], is_alive: bool) -> None:
        self.latency_ms = latency_ms
        self.is_alive = is_alive
        if self.device and self.device.state == DeviceState.DEVICE:
            self.update_state(self.device, self.current_path)

    def on_click(self, event) -> None:
        widget = event.widget
        if widget and widget.id == "header-device-badge":
            self.app.action_manage_devices()
        elif widget and widget.id in ("header-path", "header-stats"):
            self.app.action_quick_jump()
        elif widget and widget.id == "header-logo":
            self.app.action_show_help()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "hbtn-scrcpy":
            self.app.action_launch_scrcpy()
        elif btn_id == "hbtn-sdcard":
            self.app.load_directory("/sdcard")
        elif btn_id == "hbtn-extsd":
            if self.device and self.device.ext_sd_path:
                self.app.load_directory(self.device.ext_sd_path)
            else:
                self.app.show_no_microsd_toast()
        elif btn_id == "hbtn-lang":
            self.app.action_toggle_language()
