"""
Main Textual Application for AndroidTUI.
Coordinates the ADB manager, Miller Columns browser, Disconnected Dashboard,
and interactive modals.
"""
import os
from pathlib import Path
from typing import Optional, List

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable
from textual import work

from .adb import AdbManager
from .models import AdbDevice, ConnectionType, DeviceState, FileEntry, FileCategory
from .theme import APP_CSS, is_text_previewable
from .image_preview import load_image_thumbnail
from .device_store import save_remembered_device, load_remembered_devices, clear_remembered_devices
from .views.header import HeaderBar
from .views.footer import FooterBar
from .views.disconnected import DisconnectedDashboard
from .views.browser import BrowserView
from .views.modals import (
    WirelessConnectModal,
    WirelessPairModal,
    DeviceSelectModal,
    DownloadModal,
    BatchDownloadModal,
    UploadModal,
    CreateFolderModal,
    RenameModal,
    DeleteConfirmModal,
    HelpModal,
)


class AndroidTuiApp(App):
    """Modern Android ADB File Manager TUI with PikPakTUI styling."""

    CSS = APP_CSS
    TITLE = "AndroidTUI"
    SUB_TITLE = "ADB Terminal User Interface"

    BINDINGS = [
        Binding("q", "quit_app", "Esci", show=True),
        Binding("question_mark", "show_help", "Aiuto", show=True),
        Binding("c", "manage_devices", "Dispositivi", show=True),
        Binding("r", "refresh_view", "Ricarica", show=True),
        Binding("space", "toggle_selection", "Seleziona", show=True),
        Binding("a", "toggle_select_all", "Tutti", show=True),
        Binding("d", "download_entry", "Scarica", show=True),
        Binding("u", "upload_entry", "Carica", show=True),
        Binding("f", "create_folder", "Nuova cartella", show=True),
        Binding("n", "rename_entry", "Rinomina", show=True),
        Binding("x", "delete_entry", "Elimina", show=True),
        Binding("enter", "enter_selected", "Apri", show=True),
        Binding("l", "enter_selected", "Apri", show=False),
        Binding("backspace", "go_parent", "Genitore", show=True),
        Binding("h", "go_parent", "Genitore", show=False),
        Binding("j", "cursor_down", "Giù", show=False),
        Binding("k", "cursor_up", "Su", show=False),
    ]

    def __init__(self, custom_adb_path: Optional[str] = None):
        super().__init__()
        self.adb = AdbManager(custom_adb_path)
        self.current_path: str = "/sdcard"
        self.parent_path: str = "/"
        self.default_pc_download_dir: str = str(Path.home() / "Downloads" / "AndroidTUI")
        self.active_entries: List[FileEntry] = []
        self.parent_entries: List[FileEntry] = []
        self.selected_paths: set = set()
        self.selected_entries: dict = {}
        self._stability_timer = None


    def compose(self) -> ComposeResult:
        yield HeaderBar()
        yield DisconnectedDashboard()
        yield BrowserView()
        yield FooterBar()

    def on_mount(self) -> None:
        # Initially hide browser view until a connected device is active
        self.query_one(BrowserView).display = False
        self.query_one(DisconnectedDashboard).display = True
        self._stability_timer = self.set_interval(4.0, self.check_connection_stability)
        self.scan_and_auto_connect()

    # -------------------------------------------------------------
    # State synchronization & UI toggles
    # -------------------------------------------------------------
    def sync_views(self) -> None:
        header = self.query_one(HeaderBar)
        browser = self.query_one(BrowserView)
        disconnected = self.query_one(DisconnectedDashboard)

        device = self.adb.active_device
        is_ready = device is not None and device.state == DeviceState.DEVICE

        header.update_state(device, self.current_path if is_ready else "")

        if is_ready:
            disconnected.display = False
            browser.display = True
        else:
            browser.display = False
            disconnected.display = True

    # -------------------------------------------------------------
    # Background worker tasks for ADB
    # -------------------------------------------------------------
    @work(thread=True)
    def scan_and_auto_connect(self) -> None:
        if self.adb.demo_mode:
            return
        devices = self.adb.get_devices()
        if self.adb.demo_mode:
            return
        ready_devs = [d for d in devices if d.state == DeviceState.DEVICE]

        if ready_devs:
            # Auto-select the first ready device
            self.adb.set_active_device(ready_devs[0])
            self.app.call_from_thread(self._on_device_connected, ready_devs[0])
        elif devices:
            # Found device but offline/unauthorized
            self.adb.set_active_device(devices[0])
            self.app.call_from_thread(self._on_device_unready, devices[0])
        else:
            self.adb.set_active_device(None)
            self.app.call_from_thread(self.sync_views)

    def _on_device_connected(self, device: AdbDevice) -> None:
        self.sync_views()
        self.query_one(FooterBar).show_toast(f"Connesso a {device.display_name}")
        # Remember device in persistent storage
        if device.connection_type == ConnectionType.WIRELESS:
            save_remembered_device(device.serial, device.display_name, "wireless")
        elif device.connection_type == ConnectionType.USB:
            save_remembered_device(device.serial, device.display_name, "usb")
        self.load_directory(self.current_path)

    def _on_device_unready(self, device: AdbDevice) -> None:
        self.sync_views()
        if device.state == DeviceState.UNAUTHORIZED:
            self.query_one(FooterBar).show_toast(f"Dispositivo non autorizzato: accetta RSA sullo schermo del telefono", is_error=True)
        elif device.state == DeviceState.OFFLINE:
            self.query_one(FooterBar).show_toast(f"Dispositivo offline: ricollega cavo o riavvia ADB", is_error=True)

    @work(thread=True)
    def load_directory(self, path: str) -> None:
        entries, err = self.adb.list_directory(path)
        if err:
            self.app.call_from_thread(self.query_one(FooterBar).show_toast, err, True)
            return

        # Calculate parent path
        clean = path.rstrip("/")
        parent = clean.rsplit("/", 1)[0] if "/" in clean else "/"
        if not parent:
            parent = "/"

        parent_entries, _ = self.adb.list_directory(parent) if parent != clean else ([], None)

        self.current_path = clean or "/"
        self.parent_path = parent
        self.active_entries = entries
        self.parent_entries = parent_entries
        self.selected_paths.clear()
        self.selected_entries.clear()

        self.app.call_from_thread(self._apply_directory_data, clean or "/", entries, parent, parent_entries)

    def _apply_directory_data(
        self,
        current_path: str,
        entries: List[FileEntry],
        parent_path: str,
        parent_entries: List[FileEntry],
    ) -> None:
        browser = self.query_one(BrowserView)
        browser.update_browser(current_path, entries, parent_path, parent_entries, self.selected_paths)
        self.query_one(HeaderBar).update_state(self.adb.active_device, current_path)
        self.query_one(FooterBar).update_batch_selection(0, "")
        self.query_one(FooterBar).show_toast(f"{len(entries)} elementi caricati")

        # Load preview for first item if applicable
        if entries and not entries[0].is_dir:
            if entries[0].category == FileCategory.IMAGE:
                self.fetch_image_preview(entries[0])
            elif is_text_previewable(entries[0].name, entries[0].is_dir):
                self.fetch_preview(entries[0])

    @work(thread=True)
    def fetch_preview(self, entry: FileEntry) -> None:
        if entry.is_dir or not is_text_previewable(entry.name, entry.is_dir):
            return
        preview_text, _ = self.adb.read_text_preview(entry.path)
        self.app.call_from_thread(self._update_preview_display, entry, preview_text)

    def _update_preview_display(self, entry: FileEntry, preview_text: str) -> None:
        selected = self.get_selected_entry()
        if selected and selected.path == entry.path:
            browser = self.query_one(BrowserView)
            browser.set_selected_entry(entry, preview_text=preview_text)

    @work(thread=True)
    def fetch_image_preview(self, entry: FileEntry) -> None:
        if entry.is_dir or entry.category != FileCategory.IMAGE:
            return
        text_render, dim_str = load_image_thumbnail(entry.path, self.adb, max_width=30, max_height=14)
        self.app.call_from_thread(self._update_image_preview_display, entry, text_render, dim_str)

    def _update_image_preview_display(self, entry: FileEntry, text_render, dim_str: Optional[str]) -> None:
        selected = self.get_selected_entry()
        if selected and selected.path == entry.path:
            browser = self.query_one(BrowserView)
            browser.set_selected_entry(entry, image_render=text_render, image_dim=dim_str)

    # -------------------------------------------------------------
    # Navigation and selection events
    # -------------------------------------------------------------
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self.active_entries):
            entry = self.active_entries[idx]
            if entry.is_dir or entry.is_symlink:
                self.load_directory(entry.path)
            elif entry.category == FileCategory.IMAGE:
                self.fetch_image_preview(entry)
            elif is_text_previewable(entry.name, entry.is_dir):
                self.fetch_preview(entry)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self.active_entries):
            entry = self.active_entries[idx]
            self.query_one(BrowserView).set_selected_entry(entry)
            if not entry.is_dir:
                if entry.category == FileCategory.IMAGE:
                    self.fetch_image_preview(entry)
                elif is_text_previewable(entry.name, entry.is_dir):
                    self.fetch_preview(entry)


    def action_enter_selected(self) -> None:
        table = self.query_one(DataTable)
        idx = table.cursor_row
        if 0 <= idx < len(self.active_entries):
            entry = self.active_entries[idx]
            if entry.is_dir or entry.is_symlink:
                self.load_directory(entry.path)
            else:
                self.action_download_entry()

    def action_go_parent(self) -> None:
        if self.current_path in ("/", "/sdcard"):
            if self.current_path == "/sdcard":
                self.load_directory("/")
            return
        parent = self.current_path.rsplit("/", 1)[0] or "/"
        self.load_directory(parent)

    def action_cursor_down(self) -> None:
        table = self.query_one(DataTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        table = self.query_one(DataTable)
        table.action_cursor_up()

    def action_refresh_view(self) -> None:
        if self.adb.active_device:
            self.load_directory(self.current_path)
            self.query_one(FooterBar).show_toast("Ricaricato.")
        else:
            self.scan_and_auto_connect()

    # -------------------------------------------------------------
    # Batch Selection & Multi-file Operations
    # -------------------------------------------------------------
    def action_toggle_selection(self) -> None:
        """Toggles batch selection of currently highlighted entry."""
        entry = self.get_selected_entry()
        if not entry:
            return
        if entry.path in self.selected_paths:
            self.selected_paths.remove(entry.path)
            self.selected_entries.pop(entry.path, None)
        else:
            self.selected_paths.add(entry.path)
            self.selected_entries[entry.path] = entry
        self._refresh_selection_state()

    def action_toggle_select_all(self) -> None:
        """Selects or deselects all files in current directory."""
        files = [e for e in self.active_entries if not e.is_dir]
        if not files:
            return
        if all(e.path in self.selected_paths for e in files):
            for e in files:
                self.selected_paths.discard(e.path)
                self.selected_entries.pop(e.path, None)
        else:
            for e in files:
                self.selected_paths.add(e.path)
                self.selected_entries[e.path] = e
        self._refresh_selection_state()

    def _refresh_selection_state(self) -> None:
        browser = self.query_one(BrowserView)
        browser.update_browser(
            self.current_path,
            self.active_entries,
            self.parent_path,
            self.parent_entries,
            self.selected_paths,
        )
        count = len(self.selected_paths)
        total_bytes = sum(e.size for e in self.selected_entries.values())
        total_str = self._format_size(total_bytes)
        self.query_one(FooterBar).update_batch_selection(count, total_str)

    def _format_size(self, size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    # -------------------------------------------------------------
    # Connection Stability Monitor (Ping / Heartbeat)
    # -------------------------------------------------------------
    @work(thread=True)
    def check_connection_stability(self) -> None:
        """Periodically measures ADB round-trip latency and connection stability."""
        if not self.adb.active_device or self.adb.active_device.state != DeviceState.DEVICE:
            return
        if self.adb.demo_mode:
            self.app.call_from_thread(self.query_one(HeaderBar).update_stability, 14, True)
            return

        import time
        t0 = time.perf_counter()
        code, stdout, stderr = self.adb.run_cmd(["shell", "echo 1"], timeout=3)
        latency_ms = int((time.perf_counter() - t0) * 1000)

        if code == 0:
            self.app.call_from_thread(self.query_one(HeaderBar).update_stability, latency_ms, True)
        else:
            self.app.call_from_thread(self.query_one(HeaderBar).update_stability, None, False)
            self.app.call_from_thread(self._on_connection_lost)

    def _on_connection_lost(self) -> None:
        self.query_one(FooterBar).show_toast("Connessione col dispositivo persa!", is_error=True)
        self.adb.set_active_device(None)
        self.sync_views()

    # -------------------------------------------------------------
    # File Operations (Download, Upload, Mkdir, Rename, Delete)
    # -------------------------------------------------------------
    def get_selected_entry(self) -> Optional[FileEntry]:
        table = self.query_one(DataTable)
        idx = table.cursor_row
        if 0 <= idx < len(self.active_entries):
            return self.active_entries[idx]
        return None

    def action_download_entry(self) -> None:
        """Pulls selected file(s) from Phone to PC via ADB pull (single or batch)"""
        if self.selected_paths:
            # Batch mode
            entries_to_download = list(self.selected_entries.values())
            def handle_batch(pc_dest_dir: Optional[str]) -> None:
                if not pc_dest_dir:
                    return
                self._do_batch_pull_worker(entries_to_download, pc_dest_dir)

            self.push_screen(
                BatchDownloadModal(entries=entries_to_download, default_pc_dir=self.default_pc_download_dir),
                handle_batch,
            )
            return

        entry = self.get_selected_entry()
        if not entry:
            self.query_one(FooterBar).show_toast("Nessun file selezionato per il download", is_error=True)
            return

        def handle_download(pc_dest_dir: Optional[str]) -> None:
            if not pc_dest_dir:
                return
            self._do_pull_worker(entry.path, pc_dest_dir)

        self.push_screen(
            DownloadModal(
                remote_name=entry.name,
                remote_path=entry.path,
                default_pc_dir=self.default_pc_download_dir,
            ),
            handle_download,
        )

    @work(thread=True)
    def _do_pull_worker(self, remote_path: str, pc_dest_dir: str) -> None:
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, f"Download in corso: {os.path.basename(remote_path)}...")
        success, msg = self.adb.pull_file(remote_path, pc_dest_dir)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)

    @work(thread=True)
    def _do_batch_pull_worker(self, entries: List[FileEntry], pc_dest_dir: str) -> None:
        total = len(entries)
        success_count = 0
        for idx, entry in enumerate(entries, 1):
            self.app.call_from_thread(
                self.query_one(FooterBar).show_toast,
                f"Download batch ({idx}/{total}): {entry.name}...",
            )
            success, _ = self.adb.pull_file(entry.path, pc_dest_dir)
            if success:
                success_count += 1

        msg = f"Download batch completato: {success_count}/{total} file scaricati in {pc_dest_dir}"
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, success_count == 0)
        self.selected_paths.clear()
        self.selected_entries.clear()
        self.app.call_from_thread(self._refresh_selection_state)

    def action_upload_entry(self) -> None:
        """Pushes file from PC to Phone via ADB push"""
        def handle_upload(pc_file: Optional[str]) -> None:
            if not pc_file:
                return
            self._do_push_worker(pc_file, self.current_path)

        self.push_screen(UploadModal(current_phone_dir=self.current_path), handle_upload)

    @work(thread=True)
    def _do_push_worker(self, pc_file: str, phone_dest: str) -> None:
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, f"Caricamento in corso: {os.path.basename(pc_file)}...")
        success, msg = self.adb.push_file(pc_file, phone_dest)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)
        if success:
            self.load_directory(self.current_path)

    def action_create_folder(self) -> None:
        def handle_new_folder(folder_name: Optional[str]) -> None:
            if not folder_name:
                return
            self._do_mkdir_worker(self.current_path, folder_name)

        self.push_screen(CreateFolderModal(), handle_new_folder)

    @work(thread=True)
    def _do_mkdir_worker(self, parent: str, folder_name: str) -> None:
        success, msg = self.adb.create_directory(parent, folder_name)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)
        if success:
            self.load_directory(self.current_path)

    def action_rename_entry(self) -> None:
        entry = self.get_selected_entry()
        if not entry:
            return

        def handle_rename(new_name: Optional[str]) -> None:
            if not new_name or new_name == entry.name:
                return
            self._do_rename_worker(entry.path, new_name)

        self.push_screen(RenameModal(current_name=entry.name), handle_rename)

    @work(thread=True)
    def _do_rename_worker(self, old_path: str, new_name: str) -> None:
        success, msg = self.adb.rename_entry(old_path, new_name)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)
        if success:
            self.load_directory(self.current_path)

    def action_delete_entry(self) -> None:
        entry = self.get_selected_entry()
        if not entry:
            return

        def handle_delete(confirmed: bool) -> None:
            if not confirmed:
                return
            self._do_delete_worker(entry.path)

        self.push_screen(DeleteConfirmModal(target_path=entry.path, is_dir=entry.is_dir), handle_delete)

    @work(thread=True)
    def _do_delete_worker(self, target_path: str) -> None:
        success, msg = self.adb.delete_entry(target_path)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)
        if success:
            self.load_directory(self.current_path)

    # -------------------------------------------------------------
    # Device Management & Mouse Interactions
    # -------------------------------------------------------------
    def action_manage_devices(self) -> None:
        devices = self.adb.get_devices()
        if not devices:
            self.query_one(FooterBar).show_toast("Nessun dispositivo rilevato. Usa il menu di connessione USB o WiFi.", is_error=True)
            self.sync_views()
            return

        def handle_device_select(selected_dev: Optional[AdbDevice]) -> None:
            if selected_dev:
                self.adb.set_active_device(selected_dev)
                if selected_dev.state == DeviceState.DEVICE:
                    self._on_device_connected(selected_dev)
                else:
                    self._on_device_unready(selected_dev)

        self.push_screen(DeviceSelectModal(devices=devices), handle_device_select)

    def on_button_pressed(self, event) -> None:
        btn_id = event.button.id or ""

        # Footer mouse buttons
        if btn_id == "fbtn-enter":
            self.action_enter_selected()
        elif btn_id == "fbtn-select":
            self.action_toggle_selection()
        elif btn_id == "fbtn-download":
            self.action_download_entry()
        elif btn_id == "fbtn-upload":
            self.action_upload_entry()
        elif btn_id == "fbtn-mkdir":
            self.action_create_folder()
        elif btn_id == "fbtn-rename":
            self.action_rename_entry()
        elif btn_id == "fbtn-delete":
            self.action_delete_entry()
        elif btn_id == "fbtn-devices":
            self.action_manage_devices()
        elif btn_id == "fbtn-refresh":
            self.action_refresh_view()
        elif btn_id == "fbtn-help":
            self.action_show_help()
        elif btn_id == "fbtn-quit":
            self.action_quit_app()

        # Disconnected Dashboard remembered device 1-click reconnect
        elif btn_id.startswith("btn-recon-"):
            try:
                idx = int(btn_id.split("-")[-1])
                remembered = load_remembered_devices()
                if 0 <= idx < len(remembered):
                    target_ip_port = remembered[idx].get("ip_port") or remembered[idx].get("serial")
                    if target_ip_port:
                        self.query_one(FooterBar).show_toast(f"Riconnessione rapida a {target_ip_port}...")
                        self._do_wifi_connect_worker(target_ip_port)
            except Exception as e:
                self.query_one(FooterBar).show_toast(f"Errore riconnessione: {e}", is_error=True)

        elif btn_id == "btn-clear-history":
            clear_remembered_devices()
            self.query_one(FooterBar).show_toast("Cronologia dispositivi cancellata.")
            self.sync_views()

        # USB options
        elif btn_id == "btn-usb-detect":
            self.query_one(FooterBar).show_toast("Rilevamento dispositivi USB in corso...")
            self.scan_and_auto_connect()

        elif btn_id == "btn-usb-reconnect":
            self.query_one(FooterBar).show_toast("Richiesta di riconnessione inviata ad ADB...")
            self._do_reconnect_worker()

        # Wireless manual addition
        elif btn_id == "btn-wifi-connect":
            def on_wifi_addr(addr: Optional[str]) -> None:
                if addr:
                    self._do_wifi_connect_worker(addr)
            self.push_screen(WirelessConnectModal(), on_wifi_addr)

        elif btn_id == "btn-wifi-pair":
            def on_pair_data(data: Optional[tuple]) -> None:
                if data:
                    addr, code = data
                    self._do_wifi_pair_worker(addr, code)
            self.push_screen(WirelessPairModal(), on_pair_data)

        # ADB server tools
        elif btn_id == "btn-restart-adb":
            self.query_one(FooterBar).show_toast("Riavvio del server ADB in corso...")
            self._do_restart_adb_worker()

        elif btn_id == "btn-tcpip":
            self._do_tcpip_worker()

        elif btn_id == "btn-start-demo":
            self.adb.set_active_device(
                AdbDevice(
                    serial="demo-pixel-8",
                    state=DeviceState.DEVICE,
                    connection_type=ConnectionType.DEMO,
                    model="Pixel 8 Pro (Demo Mode)",
                    brand="Google",
                    android_version="14",
                    sdk_version="34",
                    battery_level=88,
                    battery_status="In carica",
                    storage_free="64.5 GB",
                    storage_total="128 GB",
                )
            )
            self._on_device_connected(self.adb.active_device)


    @work(thread=True)
    def _do_reconnect_worker(self) -> None:
        success, msg = self.adb.reconnect_devices()
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)
        self.scan_and_auto_connect()

    @work(thread=True)
    def _do_wifi_connect_worker(self, addr: str) -> None:
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, f"Connessione a {addr}...")
        success, msg = self.adb.wireless_connect(addr)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)
        self.scan_and_auto_connect()

    @work(thread=True)
    def _do_wifi_pair_worker(self, addr: str, code: str) -> None:
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, f"Accoppiamento con {addr}...")
        success, msg = self.adb.wireless_pair(addr, code)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)
        if success:
            # Auto-connect after pairing
            self._do_wifi_connect_worker(addr)

    @work(thread=True)
    def _do_restart_adb_worker(self) -> None:
        success, msg = self.adb.restart_server()
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)
        self.scan_and_auto_connect()

    @work(thread=True)
    def _do_tcpip_worker(self) -> None:
        success, msg = self.adb.enable_tcpip_mode(5555)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)

    def action_show_help(self) -> None:
        self.push_screen(HelpModal())

    def action_quit_app(self) -> None:
        self.exit()


def main() -> None:
    import sys
    import argparse

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="AndroidTUI — Interfaccia Terminale per la gestione del file system Android via ADB"
    )
    parser.add_argument(
        "--adb-path",
        help="Percorso personalizzato dell'eseguibile adb.exe",
        default=None,
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Avvia direttamente in modalità simulazione / demo",
    )
    args = parser.parse_args()

    app = AndroidTuiApp(custom_adb_path=args.adb_path)
    if args.demo:
        from .models import AdbDevice, ConnectionType, DeviceState
        app.adb.set_active_device(
            AdbDevice(
                serial="demo-pixel-8",
                state=DeviceState.DEVICE,
                connection_type=ConnectionType.DEMO,
                model="Pixel 8 Pro (Demo Mode)",
                brand="Google",
                android_version="14",
                sdk_version="34",
                battery_level=88,
                battery_status="In carica",
                storage_free="64.5 GB",
                storage_total="128 GB",
            )
        )

    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)

