"""
Disconnected state dashboard for AndroidTUI.
Shown when no ready ADB device is connected.
Provides interactive options for USB debugging, Wireless debugging, ADB server diagnostics, and Demo mode.
"""
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button


class DisconnectedDashboard(Container):
    """Interactive fallback dashboard displaying connection options when device is not connected."""

    def __init__(self, **kwargs):
        super().__init__(id="disconnected-container", **kwargs)

    def compose(self) -> ComposeResult:
        with Vertical(id="disconnected-hero"):
            yield Static("⚡ Android Debug Bridge — Connessione Dispositivo", id="hero-title")
            yield Static("⚠️ Nessun dispositivo Android rilevato in modalità 'device'. Scegli una modalità di connessione:", id="hero-subtitle")

            with Horizontal(classes="connection-options-grid"):
                # Option 1: USB Connection
                with Vertical(classes="option-card"):
                    yield Static("🔌 Opzione 1: Collegamento USB", classes="card-title")
                    yield Static(
                        "1. Collega il telefono al PC con cavo USB.\n"
                        "2. Vai in Impostazioni > Opzioni sviluppatore > attiva [bold]Debug USB[/].\n"
                        "3. Sul display del telefono tocca [bold]'Consenti sempre da questo computer'[/].",
                        classes="card-desc",
                    )
                    with Horizontal(classes="button-bar"):
                        yield Button("Cerca Dispositivi USB", id="btn-usb-detect", variant="primary")
                        yield Button("Riconnetti Offline", id="btn-usb-reconnect")

                # Option 2: Wireless Debugging
                with Vertical(classes="option-card"):
                    yield Static("📶 Opzione 2: Debug Wireless", classes="card-title")
                    yield Static(
                        "1. Assicurati che PC e telefono siano sulla stessa rete Wi-Fi.\n"
                        "2. Vai in Opzioni sviluppatore > [bold]Debug wireless[/].\n"
                        "3. Usa 'Accoppia con codice' al primo avvio, poi 'Connetti' all'IP:Porta.",
                        classes="card-desc",
                    )
                    with Horizontal(classes="button-bar"):
                        yield Button("Connetti IP:Porta", id="btn-wifi-connect", variant="primary")
                        yield Button("Accoppia (Pair)", id="btn-wifi-pair")

            with Horizontal(classes="connection-options-grid"):
                # Option 3: ADB Tools
                with Vertical(classes="option-card"):
                    yield Static("🔄 Diagnostica & Server ADB", classes="card-title")
                    yield Static(
                        "Se i dispositivi risultano 'offline' o non rispondono, riavvia il demone locale ADB sul computer oppure attiva la modalità TCP/IP su porta 5555.",
                        classes="card-desc",
                    )
                    with Horizontal(classes="button-bar"):
                        yield Button("Riavvia Server ADB", id="btn-restart-adb")
                        yield Button("Attiva TCP/IP (5555)", id="btn-tcpip")

                # Option 4: Demo Simulation
                with Vertical(classes="option-card"):
                    yield Static("🎮 Modalità Demo / Test UI", classes="card-title")
                    yield Static(
                        "Vuoi provare subito la TUI senza collegare fisicamente un telefono? Esplora un file system simulato ispirato a pikpaktui.",
                        classes="card-desc",
                    )
                    with Horizontal(classes="button-bar"):
                        yield Button("Esplora in Demo", id="btn-start-demo", variant="primary")
