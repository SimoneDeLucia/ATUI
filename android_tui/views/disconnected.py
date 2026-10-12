"""
Disconnected state dashboard for AndroidTUI.
Shown when no ready ADB device is connected.
Provides interactive options for USB debugging, remembered Wireless devices with 1-click reconnect,
manual IP:Port / pairing, ADB server diagnostics, Demo mode, and i18n support.
"""
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button

from ..device_store import load_remembered_devices
from ..i18n import t


class DisconnectedDashboard(Container):
    """Interactive fallback dashboard displaying connection options and remembered devices."""

    def __init__(self, **kwargs):
        super().__init__(id="disconnected-container", **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(id="disconnected-hero"):
            yield Static(t("dash_hero_title"), id="hero-title")
            yield Static(t("dash_hero_subtitle"), id="hero-subtitle")

            with Horizontal(classes="connection-options-grid"):
                # Option 1: USB Connection
                with Vertical(classes="option-card"):
                    yield Static(t("dash_card_usb_title"), classes="card-title")
                    yield Static(t("dash_card_usb_desc"), classes="card-desc")
                    with Horizontal(classes="button-bar"):
                        yield Button(t("dash_btn_usb_detect"), id="btn-usb-detect", variant="primary")
                        yield Button(t("dash_btn_usb_reconnect"), id="btn-usb-reconnect")

                # Option 2: Wireless Debugging & Remembered Devices
                with Vertical(classes="option-card", id="card-wireless"):
                    yield Static(t("dash_card_wifi_title"), classes="card-title")
                    remembered = load_remembered_devices()
                    if remembered:
                        yield Static(f"[bold #7dcfff]{t('dash_recent_title')}:[/] (1-click)", classes="card-desc")
                        for idx, dev in enumerate(remembered[:4]):
                            name = dev.get("name") or "Android Device"
                            ip_port = dev.get("ip_port") or dev.get("serial") or ""
                            last_seen = dev.get("last_seen", "")
                            label_str = f"📶 {name} · {ip_port} ({last_seen})" if last_seen else f"📶 {name} · {ip_port}"
                            yield Button(label_str, id=f"btn-recon-{idx}", classes="btn-remembered", variant="primary")
                    else:
                        yield Static(f"[dim]{t('dash_card_wifi_desc')}[/]", classes="card-desc")

                    with Horizontal(classes="button-bar"):
                        yield Button(t("dash_btn_wifi_connect"), id="btn-wifi-connect")
                        yield Button(t("dash_btn_wifi_pair"), id="btn-wifi-pair")
                        if remembered:
                            yield Button(t("dash_btn_clear_history"), id="btn-clear-history")

            with Horizontal(classes="connection-options-grid"):
                # Option 3: ADB Tools
                with Vertical(classes="option-card"):
                    yield Static(t("dash_card_tools_title"), classes="card-title")
                    yield Static(t("dash_card_tools_desc"), classes="card-desc")
                    with Horizontal(classes="button-bar"):
                        yield Button(t("dash_btn_restart_adb"), id="btn-restart-adb")
                        yield Button(t("dash_btn_tcpip"), id="btn-tcpip")

                # Option 4: Demo Simulation
                with Vertical(classes="option-card"):
                    yield Static("🎮 Demo / UI Test", classes="card-title")
                    yield Static("Google Pixel 8 Pro simulation mode with full image preview and file browsing.", classes="card-desc")
                    with Horizontal(classes="button-bar"):
                        yield Button(t("dash_btn_demo"), id="btn-start-demo", variant="primary")

    def update_texts(self) -> None:
        """Refreshes text labels when language is toggled."""
        hero_title = self.query_one("#hero-title", Static)
        hero_sub = self.query_one("#hero-subtitle", Static)
        hero_title.update(t("dash_hero_title"))
        hero_sub.update(t("dash_hero_subtitle"))
