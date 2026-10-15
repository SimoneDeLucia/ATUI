"""
Disconnected state dashboard for AndroidTUI.
Shown when no ready ADB device is connected.
Provides a unified 3-column Miller-columns interface matching the connected layout:
- Left pane (where parent folders usually are): USB and WiFi connection controls and recent devices history.
- Center pane (where current folder files usually are): Connection hero status, guided steps and shortcuts.
- Right pane (where previews usually are): ADB server diagnostics and debug tools.
"""
from textual.app import ComposeResult
from textual.containers import VerticalScroll, Horizontal, Vertical
from textual.widgets import Static, Button

from ..device_store import load_remembered_devices
from ..i18n import t


class DisconnectedDashboard(Horizontal):
    """Interactive 3-column dashboard displaying USB, Wireless connection options, recent devices, and ADB debug tools."""

    def __init__(self, **kwargs):
        super().__init__(id="disconnected-container", **kwargs)

    def compose(self) -> ComposeResult:
        # Column 1: Left Pane (where parent folders usually are)
        # Contains: USB connection, WiFi connection, and Recent devices history
        with Vertical(id="disconnected-left-pane", classes="pane"):
            yield Static(t("dash_left_pane_title"), id="disconnected-left-title", classes="pane-title meta-key")
            with VerticalScroll(classes="disconnected-scroll", id="disconnected-left-scroll"):
                # USB Option
                with Vertical(classes="option-card", id="card-usb"):
                    yield Static(t("dash_card_usb_title"), id="card-usb-title", classes="card-title")
                    yield Static(t("dash_card_usb_desc"), id="card-usb-desc", classes="card-desc")
                    with Horizontal(classes="card-button-bar"):
                        yield Button(t("dash_btn_usb_detect"), id="btn-usb-detect", variant="primary")
                        yield Button(t("dash_btn_usb_reconnect"), id="btn-usb-reconnect")

                # Wireless Option
                with Vertical(classes="option-card", id="card-wireless"):
                    yield Static(t("dash_card_wifi_title"), id="card-wifi-title", classes="card-title")
                    yield Static(t("dash_card_wifi_desc"), id="card-wifi-desc", classes="card-desc")
                    with Horizontal(classes="card-button-bar"):
                        yield Button(t("dash_btn_wifi_connect"), id="btn-wifi-connect", variant="primary")
                        yield Button(t("dash_btn_wifi_pair"), id="btn-wifi-pair")

                # Recent Devices (History)
                with Vertical(classes="option-card", id="card-recent"):
                    yield Static(t("dash_card_recent_title"), id="card-recent-title", classes="card-title")
                    yield Static(t("dash_card_recent_desc"), id="card-recent-desc", classes="card-desc")
                    remembered = load_remembered_devices()
                    if remembered:
                        with Vertical(id="recent-devices-list"):
                            for idx, dev in enumerate(remembered):
                                name = dev.get("name") or "Android Device"
                                dev_type = dev.get("type", "wireless")
                                icon = "🔌" if dev_type == "usb" else "📶"
                                type_tag = "USB" if dev_type == "usb" else "WiFi"
                                ip_or_serial = dev.get("ip_port") or dev.get("serial") or ""
                                last_seen = dev.get("last_seen", "")

                                label_str = f"{icon} [{type_tag}] {name} · {ip_or_serial} ({last_seen})" if last_seen else f"{icon} [{type_tag}] {name} · {ip_or_serial}"

                                with Horizontal(classes="recent-device-row"):
                                    yield Button(label_str, id=f"btn-recon-{idx}", classes="btn-remembered-item", variant="primary")
                                    yield Button(t("dash_btn_remove_device"), id=f"btn-del-recent-{idx}", classes="btn-del-item")

                        with Horizontal(classes="card-button-bar", id="recent-actions-bar"):
                            yield Button(t("dash_btn_clear_history"), id="btn-clear-history")
                    else:
                        yield Static(f"[dim]{t('dash_no_recent')}[/]", id="recent-empty-label", classes="card-desc")

        # Column 2: Center Pane (where content directory usually is)
        # Contains: Header banner, connection steps guide and shortcuts
        with Vertical(id="disconnected-center-pane", classes="pane"):
            yield Static(t("dash_center_pane_title"), id="disconnected-center-title", classes="pane-title meta-key")
            with VerticalScroll(classes="disconnected-scroll", id="disconnected-center-scroll"):
                with Vertical(id="disconnected-hero"):
                    yield Static(t("dash_hero_title"), id="hero-title")
                    yield Static(t("dash_hero_subtitle"), id="hero-subtitle")

                with Vertical(classes="option-card guide-card", id="card-guide-usb"):
                    yield Static(t("dash_guide_usb_title"), id="guide-usb-title", classes="card-title")
                    yield Static(t("dash_card_usb_desc"), id="guide-usb-desc", classes="card-desc")

                with Vertical(classes="option-card guide-card", id="card-guide-wifi"):
                    yield Static(t("dash_guide_wifi_title"), id="guide-wifi-title", classes="card-title")
                    yield Static(t("dash_card_wifi_desc"), id="guide-wifi-desc", classes="card-desc")

                with Vertical(classes="option-card guide-card", id="card-guide-shortcuts"):
                    yield Static(t("dash_quick_shortcuts_title"), id="guide-shortcuts-title", classes="card-title")
                    yield Static(
                        "• [b cyan][c][/] Seleziona o aggiungi dispositivo ADB\n"
                        "• [b cyan][m][/] Condivisione schermo con Scrcpy\n"
                        "• [b cyan][F2][/] Cambia lingua (Italiano / English)\n"
                        "• [b cyan][?][/] Manuale di aiuto e comandi rapidi\n"
                        "• [b cyan][q][/] Esci dall'applicazione",
                        id="guide-shortcuts-desc",
                        classes="card-desc"
                    )

        # Column 3: Right Pane (where preview pane usually is)
        # Contains: ADB Debug & Diagnostics tools, info and recovery options
        with Vertical(id="disconnected-right-pane", classes="pane"):
            yield Static(t("dash_right_pane_title"), id="disconnected-right-title", classes="pane-title meta-key")
            with VerticalScroll(classes="disconnected-scroll", id="disconnected-right-scroll"):
                with Vertical(classes="option-card", id="card-tools"):
                    yield Static(t("dash_card_tools_title"), id="card-tools-title", classes="card-title")
                    yield Static(t("dash_card_tools_desc"), id="card-tools-desc", classes="card-desc")
                    with Horizontal(classes="card-button-bar"):
                        yield Button(t("dash_btn_restart_adb"), id="btn-restart-adb", variant="warning")
                        yield Button(t("dash_btn_tcpip"), id="btn-tcpip")

                with Vertical(classes="option-card", id="card-adb-info"):
                    yield Static(t("dash_adb_info_title"), id="card-adb-info-title", classes="card-title")
                    yield Static(
                        "• Demone ADB locale: [b green]Porta 5037[/]\n"
                        "• Modalità TCP/IP predefinita: [b cyan]Porta 5555[/]\n"
                        "• Stato: [b yellow]In attesa di connessione periferica[/]",
                        id="card-adb-info-desc",
                        classes="card-desc"
                    )

                with Vertical(classes="option-card", id="card-troubleshooting"):
                    yield Static(t("dash_troubleshooting_title"), id="card-troubleshooting-title", classes="card-title")
                    yield Static(
                        "• [b yellow]Unauthorized[/]: Sblocca lo schermo e premi [i]'Consenti sempre'[/].\n"
                        "• [b red]Offline[/]: Clicca su [i]'Riavvia Server ADB'[/] per riallineare i socket.\n"
                        "• [b green]WiFi[/]: Verifica che smartphone e PC condividano lo stesso SSID.",
                        id="card-troubleshooting-desc",
                        classes="card-desc"
                    )

    def update_texts(self) -> None:
        """Refreshes all localized labels and buttons when language is toggled."""
        for q, val in [
            ("#disconnected-left-title", t("dash_left_pane_title")),
            ("#disconnected-center-title", t("dash_center_pane_title")),
            ("#disconnected-right-title", t("dash_right_pane_title")),
            ("#hero-title", t("dash_hero_title")),
            ("#hero-subtitle", t("dash_hero_subtitle")),
            ("#card-usb-title", t("dash_card_usb_title")),
            ("#card-usb-desc", t("dash_card_usb_desc")),
            ("#guide-usb-title", t("dash_guide_usb_title")),
            ("#guide-usb-desc", t("dash_card_usb_desc")),
            ("#card-wifi-title", t("dash_card_wifi_title")),
            ("#card-wifi-desc", t("dash_card_wifi_desc")),
            ("#guide-wifi-title", t("dash_guide_wifi_title")),
            ("#guide-wifi-desc", t("dash_card_wifi_desc")),
            ("#guide-shortcuts-title", t("dash_quick_shortcuts_title")),
            ("#card-recent-title", t("dash_card_recent_title")),
            ("#card-recent-desc", t("dash_card_recent_desc")),
            ("#card-tools-title", t("dash_card_tools_title")),
            ("#card-tools-desc", t("dash_card_tools_desc")),
            ("#card-adb-info-title", t("dash_adb_info_title")),
            ("#card-troubleshooting-title", t("dash_troubleshooting_title")),
        ]:
            node = self.query(q)
            if node:
                node.first().update(val)

        for btn_id, text in [
            ("#btn-usb-detect", t("dash_btn_usb_detect")),
            ("#btn-usb-reconnect", t("dash_btn_usb_reconnect")),
            ("#btn-wifi-connect", t("dash_btn_wifi_connect")),
            ("#btn-wifi-pair", t("dash_btn_wifi_pair")),
            ("#btn-clear-history", t("dash_btn_clear_history")),
            ("#btn-restart-adb", t("dash_btn_restart_adb")),
            ("#btn-tcpip", t("dash_btn_tcpip")),
        ]:
            btn = self.query(btn_id)
            if btn:
                btn.first().label = text
