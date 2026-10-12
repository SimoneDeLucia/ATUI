"""
Disconnected state dashboard for AndroidTUI.
Shown when no ready ADB device is connected.
Provides interactive options for USB debugging, remembered Wireless devices with 1-click reconnect,
manual IP:Port / pairing, ADB server diagnostics, and Demo mode.
"""
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button

from ..device_store import load_remembered_devices


class DisconnectedDashboard(Container):
    """Interactive fallback dashboard displaying connection options and remembered devices."""

    def __init__(self, **kwargs):
        super().__init__(id="disconnected-container", **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(id="disconnected-hero"):
            yield Static("⚡ Android Debug Bridge — Gestione Connessioni", id="hero-title")
            yield Static("⚠️ Nessun dispositivo attivo. Seleziona un dispositivo recente o una modalità di connessione:", id="hero-subtitle")

            with Horizontal(classes="connection-options-grid"):
                # Option 1: USB Connection
                with Vertical(classes="option-card"):
                    yield Static("🔌 Opzione 1: Collegamento USB", classes="card-title")
                    yield Static(
                        "1. Collega il telefono al PC con cavo USB.\n"
                        "2. Abilita [bold]Debug USB[/] nelle Opzioni Sviluppatore.\n"
                        "3. Autorizza l'impronta RSA del PC sul telefono.",
                        classes="card-desc",
                    )
                    with Horizontal(classes="button-bar"):
                        yield Button("Cerca Dispositivi USB", id="btn-usb-detect", variant="primary")
                        yield Button("Riconnetti Offline", id="btn-usb-reconnect")

                # Option 2: Wireless Debugging & Remembered Devices
                with Vertical(classes="option-card", id="card-wireless"):
                    yield Static("📶 Debug Wireless & Dispositivi Recenti", classes="card-title")
                    remembered = load_remembered_devices()
                    if remembered:
                        yield Static("[bold #7dcfff]Dispositivi precedentemente connessi:[/] (1-click per connettere)", classes="card-desc")
                        for idx, dev in enumerate(remembered[:4]):
                            name = dev.get("name") or "Dispositivo Android"
                            ip_port = dev.get("ip_port") or dev.get("serial") or ""
                            last_seen = dev.get("last_seen", "")
                            label_str = f"📶 {name} · {ip_port} ({last_seen})" if last_seen else f"📶 {name} · {ip_port}"
                            yield Button(label_str, id=f"btn-recon-{idx}", classes="btn-remembered", variant="primary")
                    else:
                        yield Static("[dim]Nessun dispositivo recente in memoria.[/]", classes="card-desc")

                    yield Static("[bold #e0af68]Aggiunta manuale dispositivo:[/\n]", classes="card-desc")
                    with Horizontal(classes="button-bar"):
                        yield Button("+ Inserisci IP:Porta", id="btn-wifi-connect")
                        yield Button("🔗 Accoppia con Codice", id="btn-wifi-pair")
                        if remembered:
                            yield Button("🗑️ Cancella Lista", id="btn-clear-history")


            with Horizontal(classes="connection-options-grid"):
                # Option 3: ADB Tools
                with Vertical(classes="option-card"):
                    yield Static("🔄 Diagnostica & Server ADB", classes="card-title")
                    yield Static(
                        "Riavvia il demone locale ADB sul computer oppure attiva la modalità TCP/IP su porta 5555 per il telefono collegato.",
                        classes="card-desc",
                    )
                    with Horizontal(classes="button-bar"):
                        yield Button("Riavvia Server ADB", id="btn-restart-adb")
                        yield Button("Attiva TCP/IP (5555)", id="btn-tcpip")

                # Option 4: Demo Simulation
                with Vertical(classes="option-card"):
                    yield Static("🎮 Modalità Demo / Test UI", classes="card-title")
                    yield Static(
                        "Esplora la TUI con anteprima immagini e navigazione completa in modalità simulazione (Google Pixel 8 Pro).",
                        classes="card-desc",
                    )
                    with Horizontal(classes="button-bar"):
                        yield Button("Esplora in Demo", id="btn-start-demo", variant="primary")
