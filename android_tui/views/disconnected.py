"""
Disconnected state dashboard for AndroidTUI.
Shown when no ready ADB device is connected.
Provides interactive options for USB debugging, remembered Wireless devices with 1-click reconnect,
manual IP:Port / pairing, and ADB server diagnostics with complete i18n support.
"""
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button

from ..device_store import load_remembered_devices
from ..i18n import t


class DisconnectedDashboard(Container):
    """Interactive dashboard displaying USB and Wireless connection options and ADB tools."""

    def __init__(self, **kwargs):
        super().__init__(id="disconnected-container", **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(id="disconnected-hero"):
            yield Static(t("dash_hero_title"), id="hero-title")
            yield Static(t("dash_hero_subtitle"), id="hero-subtitle")

            with Horizontal(classes="connection-options-grid"):
                # Option 1: USB Connection
                with Vertical(classes="option-card", id="card-usb"):
                    yield Static(t("dash_card_usb_title"), id="card-usb-title", classes="card-title")
                    yield Static(t("dash_card_usb_desc"), id="card-usb-desc", classes="card-desc")
                    with Horizontal(classes="card-button-bar"):
                        yield Button(t("dash_btn_usb_detect"), id="btn-usb-detect", variant="primary")
                        yield Button(t("dash_btn_usb_reconnect"), id="btn-usb-reconnect")

                # Option 2: Wireless Debugging & Remembered Devices
                with Vertical(classes="option-card", id="card-wireless"):
                    yield Static(t("dash_card_wifi_title"), id="card-wifi-title", classes="card-title")
                    remembered = load_remembered_devices()
                    if remembered:
                        yield Static(f"[bold #7dcfff]{t('dash_recent_title')}:[/] (1-click)", id="card-wifi-desc", classes="card-desc")
                        for idx, dev in enumerate(remembered[:3]):
                            name = dev.get("name") or "Android Device"
                            ip_port = dev.get("ip_port") or dev.get("serial") or ""
                            last_seen = dev.get("last_seen", "")
                            label_str = f"📶 {name} · {ip_port} ({last_seen})" if last_seen else f"📶 {name} · {ip_port}"
                            yield Button(label_str, id=f"btn-recon-{idx}", classes="btn-remembered", variant="primary")
                    else:
                        yield Static(f"[dim]{t('dash_card_wifi_desc')}[/]", id="card-wifi-desc", classes="card-desc")

                    with Horizontal(classes="card-button-bar"):
                        yield Button(t("dash_btn_wifi_connect"), id="btn-wifi-connect")
                        yield Button(t("dash_btn_wifi_pair"), id="btn-wifi-pair")
                        if remembered:
                            yield Button(t("dash_btn_clear_history"), id="btn-clear-history")

            # Option 3: ADB Diagnostics & Server Tools
            with Horizontal(classes="connection-options-grid", id="row-tools"):
                with Vertical(classes="option-card", id="card-tools"):
                    yield Static(t("dash_card_tools_title"), id="card-tools-title", classes="card-title")
                    yield Static(t("dash_card_tools_desc"), id="card-tools-desc", classes="card-desc")
                    with Horizontal(classes="card-button-bar"):
                        yield Button(t("dash_btn_restart_adb"), id="btn-restart-adb")
                        yield Button(t("dash_btn_tcpip"), id="btn-tcpip")

    def update_texts(self) -> None:
        """Refreshes all localized labels and buttons when language is toggled."""
        self.query_one("#hero-title", Static).update(t("dash_hero_title"))
        self.query_one("#hero-subtitle", Static).update(t("dash_hero_subtitle"))

        # Card USB
        self.query_one("#card-usb-title", Static).update(t("dash_card_usb_title"))
        self.query_one("#card-usb-desc", Static).update(t("dash_card_usb_desc"))
        self.query_one("#btn-usb-detect", Button).label = t("dash_btn_usb_detect")
        self.query_one("#btn-usb-reconnect", Button).label = t("dash_btn_usb_reconnect")

        # Card Wireless
        self.query_one("#card-wifi-title", Static).update(t("dash_card_wifi_title"))
        remembered = load_remembered_devices()
        wifi_desc = self.query_one("#card-wifi-desc", Static)
        if remembered:
            wifi_desc.update(f"[bold #7dcfff]{t('dash_recent_title')}:[/] (1-click)")
        else:
            wifi_desc.update(f"[dim]{t('dash_card_wifi_desc')}[/]")
        self.query_one("#btn-wifi-connect", Button).label = t("dash_btn_wifi_connect")
        self.query_one("#btn-wifi-pair", Button).label = t("dash_btn_wifi_pair")
        btn_clear = self.query("#btn-clear-history")
        if btn_clear:
            btn_clear.first().label = t("dash_btn_clear_history")

        # Card Tools
        self.query_one("#card-tools-title", Static).update(t("dash_card_tools_title"))
        self.query_one("#card-tools-desc", Static).update(t("dash_card_tools_desc"))
        self.query_one("#btn-restart-adb", Button).label = t("dash_btn_restart_adb")
        self.query_one("#btn-tcpip", Button).label = t("dash_btn_tcpip")
