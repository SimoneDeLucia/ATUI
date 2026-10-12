"""
Main Textual Application for AndroidTUI.
Coordinates the ADB manager, Miller Columns browser, Disconnected Dashboard,
and interactive modals.
"""
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List, Any, Tuple

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable
from textual import work

from .adb import AdbManager, resolve_scrcpy_path
from .models import AdbDevice, ConnectionType, DeviceState, FileEntry, FileCategory
from .theme import CSS_FILES, is_text_previewable
from .image_preview import get_file_thumbnail, load_media_thumbnail
from .device_store import save_remembered_device, load_remembered_devices, clear_remembered_devices, remove_remembered_device
from .views.header import HeaderBar
from .views.footer import FooterBar
from .views.disconnected import DisconnectedDashboard
from .views.browser import BrowserView, FileTable
from .views.modals import (
    WirelessConnectModal,
    WirelessPairModal,
    DeviceSelectModal,
    DownloadModal,
    BatchDownloadModal,
    BatchDeleteModal,
    DownloadDestinationModal,
    ColumnWidthsModal,
    UploadModal,
    CreateFolderModal,
    RenameModal,
    DeleteConfirmModal,
    HelpModal,
    QuickJumpModal,
    PathBreadcrumbsModal,
    ScrcpyModal,
    SortModal,
)
from .i18n import t, toggle_language, get_current_language


class AndroidTuiApp(App):
    """Modern Android ADB File Manager TUI with PikPakTUI styling."""

    CSS_PATH = CSS_FILES
    TITLE = "ATUI"
    SUB_TITLE = "Android Terminal User Interface"

    BINDINGS = [
        Binding("q", "quit_app", "Esci", show=True),
        Binding("question_mark", "show_help", "Aiuto", show=True),
        Binding("c", "manage_devices", "Dispositivi", show=True),
        Binding("p", "select_breadcrumb", "Percorso", show=True),
        Binding("w", "adjust_column_widths", "Colonne", show=True),
        Binding("m", "launch_scrcpy", "Scrcpy", show=True),
        Binding("g", "quick_jump", "Memorie", show=True),
        Binding("s", "cycle_sort", "Ordina", show=True),
        Binding("S", "toggle_sort_order", "Inverti ord.", show=False),
        Binding("f2", "toggle_language", "IT/EN", show=False),
        Binding("ctrl+d", "disconnect_device", "Disconnetti", show=True),
        Binding("r", "refresh_view", "Ricarica", show=True),
        Binding("space", "toggle_selection", "Seleziona", show=True),
        Binding("a", "toggle_select_all", "Tutti", show=True),
        Binding("escape", "clear_selection", "Annulla selez.", show=False),
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
        self.sort_by, self.sort_reverse, self.saved_col_widths = self._load_browser_settings()
        self._stability_timer = None

    def _load_browser_settings(self) -> Tuple[str, bool, dict]:
        settings_file = Path.home() / ".android_tui_settings.json"
        sort_by = "name"
        sort_reverse = False
        widths = {"sel": 5, "name": 34, "size": 12, "type": 12, "modified": 18, "perms": 12}
        if settings_file.exists():
            try:
                import json
                with open(settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sort_by = data.get("sort_by", "name")
                    sort_reverse = data.get("sort_reverse", False)
                    if "col_widths" in data and isinstance(data["col_widths"], dict):
                        widths.update(data["col_widths"])
            except Exception:
                pass
        return sort_by, sort_reverse, widths

    def _save_browser_settings(self) -> None:
        settings_file = Path.home() / ".android_tui_settings.json"
        try:
            import json
            data = {}
            if settings_file.exists():
                try:
                    with open(settings_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data["sort_by"] = self.sort_by
            data["sort_reverse"] = self.sort_reverse
            browser = self.query(BrowserView)
            if browser:
                data["col_widths"] = browser.first().col_widths
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield HeaderBar()
        yield DisconnectedDashboard()
        yield BrowserView()
        yield FooterBar()

    def on_mount(self) -> None:
        browser = self.query_one(BrowserView)
        browser.col_widths.update(self.saved_col_widths)
        browser.update_columns(self.sort_by, self.sort_reverse)
        browser.display = False
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
            try:
                self.run_worker(disconnected.recompose())
            except Exception:
                pass

    # -------------------------------------------------------------
    # Background worker tasks for ADB
    # -------------------------------------------------------------
    @work(thread=True)
    def scan_and_auto_connect(self, preferred_serial: Optional[str] = None) -> None:
        if self.adb.demo_mode:
            return
        devices = self.adb.get_devices()
        if self.adb.demo_mode:
            return
        ready_devs = [d for d in devices if d.state == DeviceState.DEVICE]

        target_dev = None
        if preferred_serial:
            for d in ready_devs:
                if d.serial == preferred_serial or preferred_serial in d.serial or d.display_name == preferred_serial:
                    target_dev = d
                    break
            if not target_dev:
                for d in devices:
                    if d.serial == preferred_serial or preferred_serial in d.serial or d.display_name == preferred_serial:
                        target_dev = d
                        break

        if not target_dev and ready_devs:
            target_dev = ready_devs[0]

        if target_dev:
            self.adb.set_active_device(target_dev)
            if target_dev.state == DeviceState.DEVICE:
                self.app.call_from_thread(self._on_device_connected, target_dev)
            else:
                self.app.call_from_thread(self._on_device_unready, target_dev)
        elif devices:
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

        # Sort entries according to current criteria
        entries = self._sort_entries(entries, self.sort_by, self.sort_reverse)

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

        # Load preview for first item if applicable (supports all file categories!)
        if entries and not entries[0].is_dir:
            self.fetch_thumbnail_preview(entries[0])
            if is_text_previewable(entries[0].name, entries[0].is_dir):
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
    def fetch_thumbnail_preview(self, entry: FileEntry) -> None:
        """Loads thumbnail preview: real image/video frame or cyber category card (including prod.keys 📎)."""
        if entry.is_dir:
            return
        text_render, dim_str = get_file_thumbnail(entry, self.adb, max_width=46, max_height=20)
        self.app.call_from_thread(self._update_media_preview_display, entry, text_render, dim_str)

    def _update_media_preview_display(self, entry: FileEntry, text_render, dim_str: Optional[str]) -> None:
        selected = self.get_selected_entry()
        if selected and selected.path == entry.path:
            browser = self.query_one(BrowserView)
            browser.set_selected_entry(entry, image_render=text_render, image_dim=dim_str)

    # -------------------------------------------------------------
    # Navigation and selection events
    # -------------------------------------------------------------
    def on_file_table_checkbox_toggled(self, event: FileTable.CheckboxToggled) -> None:
        """Mouse click on the row checkbox square! Toggles batch selection without moving cursor."""
        if 0 <= event.row_index < len(self.active_entries):
            entry = self.active_entries[event.row_index]
            if entry.path in self.selected_paths:
                self.selected_paths.remove(entry.path)
                self.selected_entries.pop(entry.path, None)
            else:
                self.selected_paths.add(entry.path)
                self.selected_entries[entry.path] = entry
            self._refresh_selection_state(preserve_cursor=True)

    def on_file_table_select_all_toggled(self, event: FileTable.SelectAllToggled) -> None:
        """Mouse click on the header checkbox square [✓]!"""
        self.action_toggle_select_all()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Mouse click on column headers to sort by Name, Size, Type, Date, Perms!"""
        col = event.column_index
        if col == 0:
            self.action_toggle_select_all()
        elif col == 1:
            self.sort_directory("name")
        elif col == 2:
            self.sort_directory("size")
        elif col == 3:
            self.sort_directory("type")
        elif col == 4:
            self.sort_directory("modified")
        elif col == 5:
            self.sort_directory("perms")

    def on_file_table_file_double_clicked(self, event: FileTable.FileDoubleClicked) -> None:
        """Mouse double click opens folder or launches default system file viewer!"""
        idx = event.row_index
        if 0 <= idx < len(self.active_entries):
            entry = self.active_entries[idx]
            if entry.is_dir or entry.is_symlink:
                self.load_directory(entry.path)
            else:
                self.action_open_file(entry)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Keyboard Enter opens folder or launches default system file viewer!"""
        idx = event.cursor_row
        if 0 <= idx < len(self.active_entries):
            entry = self.active_entries[idx]
            if entry.is_dir or entry.is_symlink:
                self.load_directory(entry.path)
            else:
                self.action_open_file(entry)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self.active_entries):
            entry = self.active_entries[idx]
            self.query_one(BrowserView).set_selected_entry(entry)
            if not entry.is_dir:
                self.fetch_thumbnail_preview(entry)
                if is_text_previewable(entry.name, entry.is_dir):
                    self.fetch_preview(entry)

    # -------------------------------------------------------------
    # Sorting logic & Column Sizing
    # -------------------------------------------------------------
    def _sort_entries(self, entries: List[FileEntry], sort_by: str, reverse: bool) -> List[FileEntry]:
        dirs = [e for e in entries if e.is_dir]
        files = [e for e in entries if not e.is_dir]

        if sort_by == "name":
            dirs.sort(key=lambda x: x.name.lower(), reverse=reverse)
            files.sort(key=lambda x: x.name.lower(), reverse=reverse)
        elif sort_by == "size":
            dirs.sort(key=lambda x: x.name.lower(), reverse=reverse)
            files.sort(key=lambda x: x.size, reverse=reverse)
        elif sort_by == "type":
            dirs.sort(key=lambda x: x.name.lower(), reverse=reverse)
            files.sort(key=lambda x: (x.category.value, x.extension.lower(), x.name.lower()), reverse=reverse)
        elif sort_by in ("modified", "date"):
            dirs.sort(key=lambda x: x.date_str or "", reverse=reverse)
            files.sort(key=lambda x: x.date_str or "", reverse=reverse)
        elif sort_by in ("perms", "permissions"):
            dirs.sort(key=lambda x: x.permissions or "", reverse=reverse)
            files.sort(key=lambda x: x.permissions or "", reverse=reverse)

        return dirs + files

    def sort_directory(self, column: str) -> None:
        """Sorts active entries by column and updates table with sort arrow indicators."""
        if self.sort_by == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_by = column
            self.sort_reverse = False

        self._save_browser_settings()
        self.active_entries = self._sort_entries(self.active_entries, self.sort_by, self.sort_reverse)
        browser = self.query_one(BrowserView)
        browser.update_columns(self.sort_by, self.sort_reverse)

        col_name = t(f"col_{self.sort_by}") if f"col_{self.sort_by}" in ("col_name", "col_size", "col_type", "col_modified", "col_perms") else self.sort_by
        order_name = t("order_desc") if self.sort_reverse else t("order_asc")
        self.query_one(FooterBar).show_toast(t("sorted_by", col=col_name, order=order_name))

    def action_cycle_sort(self) -> None:
        """Keyboard shortcut (s): cycles sort mode between Name -> Size -> Type -> Modified -> Perms."""
        cycle = {"name": "size", "size": "type", "type": "modified", "modified": "perms", "perms": "name"}
        next_sort = cycle.get(self.sort_by, "name")
        self.sort_directory(next_sort)

    def action_toggle_sort_order(self) -> None:
        """Keyboard shortcut (S): toggles ascending / descending sort order."""
        self.sort_reverse = not self.sort_reverse
        self._save_browser_settings()
        self.active_entries = self._sort_entries(self.active_entries, self.sort_by, self.sort_reverse)
        browser = self.query_one(BrowserView)
        browser.update_columns(self.sort_by, self.sort_reverse)
        order_name = t("order_desc") if self.sort_reverse else t("order_asc")
        col_name = t(f"col_{self.sort_by}")
        self.query_one(FooterBar).show_toast(t("sorted_by", col=col_name, order=order_name))

    def action_show_sort_modal(self) -> None:
        """Opens SortModal to let user select sorting column or invert order."""
        def on_sort_choice(choice: Optional[str]) -> None:
            if not choice:
                return
            if choice == "invert":
                self.action_toggle_sort_order()
            else:
                self.sort_directory(choice)

        self.push_screen(SortModal(current_sort=self.sort_by, is_reverse=self.sort_reverse), on_sort_choice)

    def action_adjust_column_widths(self) -> None:
        """Opens Column Widths customization modal."""
        browser = self.query_one(BrowserView)

        def on_widths_result(widths: Optional[dict]) -> None:
            if widths:
                browser.update_columns(self.sort_by, self.sort_reverse, col_widths=widths)
                self._save_browser_settings()
                self.query_one(FooterBar).show_toast("Larghezze colonne aggiornate.")

        self.push_screen(ColumnWidthsModal(current_widths=browser.col_widths), on_widths_result)

    # -------------------------------------------------------------
    # Scrcpy Screen Mirroring Integration
    # -------------------------------------------------------------
    def action_launch_scrcpy(self) -> None:
        """Launches scrcpy to mirror Android device screen in real time."""
        device = self.adb.active_device
        if not device or device.state != DeviceState.DEVICE:
            self.query_one(FooterBar).show_toast("Nessun dispositivo pronto per Scrcpy", is_error=True)
            return

        if self.adb.demo_mode:
            self.query_one(FooterBar).show_toast(t("scrcpy_demo_toast"))
            return

        scrcpy_bin = resolve_scrcpy_path()
        if not scrcpy_bin:
            self.push_screen(ScrcpyModal())
            return

        try:
            cmd = [
                scrcpy_bin,
                "-s",
                device.serial,
                "--window-title",
                f"AndroidTUI - {device.display_name}",
            ]
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            self.query_one(FooterBar).show_toast(t("scrcpy_launched", name=device.display_name))
        except Exception as e:
            self.query_one(FooterBar).show_toast(f"Errore avvio Scrcpy: {e}", is_error=True)


    def action_enter_selected(self) -> None:
        table = self.query_one(DataTable)
        idx = table.cursor_row
        if 0 <= idx < len(self.active_entries):
            entry = self.active_entries[idx]
            if entry.is_dir or entry.is_symlink:
                self.load_directory(entry.path)
            else:
                self.action_open_file(entry)

    def action_open_file(self, entry: Optional[FileEntry] = None) -> None:
        """
        Opens a file directly using the system default application (image viewer, video player,
        PDF reader, document viewer, text editor) without requiring a manual download destination.
        """
        if not entry:
            entry = self.get_selected_entry()
        if not entry or entry.is_dir:
            return

        supported_cats = {
            FileCategory.IMAGE, FileCategory.VIDEO, FileCategory.DOCUMENT,
            FileCategory.AUDIO, FileCategory.CODE, FileCategory.ARCHIVE
        }
        ext = Path(entry.name).suffix.lower()
        supported_exts = {
            ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico",
            ".mp4", ".mkv", ".avi", ".mov", ".webm", ".3gp", ".flv",
            ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
            ".pdf", ".txt", ".md", ".json", ".xml", ".html", ".csv", ".log",
            ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".tar", ".gz"
        }
        if entry.category not in supported_cats and ext not in supported_exts:
            self.query_one(FooterBar).show_toast(t("file_type_not_supported", name=entry.name), is_error=True)
            return

        self._do_open_file_worker(entry)

    @work(thread=True)
    def _do_open_file_worker(self, entry: FileEntry) -> None:
        """Pulls file to a local temp cache directory, launches OS default viewer, and deletes on exit."""
        import tempfile
        import time
        import shutil

        self.app.call_from_thread(
            self.query_one(FooterBar).start_progress,
            1.0,
            t("opening_file", name=entry.name)
        )

        temp_dir = Path(tempfile.gettempdir()) / "atui_preview_cache"
        temp_dir.mkdir(parents=True, exist_ok=True)
        local_target = temp_dir / entry.name

        success, msg = self.adb.pull_file(entry.path, str(local_target))
        self.app.call_from_thread(self.query_one(FooterBar).update_progress, 1.0)
        self.app.call_from_thread(self.query_one(FooterBar).finish_progress)

        if success and local_target.exists():
            try:
                proc = None
                if sys.platform == "win32":
                    proc = subprocess.Popen(["cmd", "/c", f'start "" /wait "{local_target}"'], shell=True)
                elif sys.platform == "darwin":
                    proc = subprocess.Popen(["open", "-W", str(local_target)])
                else:
                    proc = subprocess.Popen(["xdg-open", str(local_target)])

                self.app.call_from_thread(
                    self.query_one(FooterBar).show_toast,
                    t("opened_file", name=entry.name)
                )

                if proc:
                    proc.wait()

                # Remove temporary preview file once viewer process closes
                for _ in range(15):
                    try:
                        if local_target.exists():
                            if local_target.is_file():
                                local_target.unlink()
                            elif local_target.is_dir():
                                shutil.rmtree(local_target, ignore_errors=True)
                        break
                    except Exception:
                        time.sleep(1.0)
            except Exception as e:
                self.app.call_from_thread(
                    self.query_one(FooterBar).show_toast,
                    f"Errore avvio app di sistema: {e}",
                    True
                )
        else:
            self.app.call_from_thread(
                self.query_one(FooterBar).show_toast,
                f"Errore apertura: {msg}",
                True
            )

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
        """Toggles batch selection of currently highlighted entry without moving cursor."""
        entry = self.get_selected_entry()
        if not entry:
            return
        if entry.path in self.selected_paths:
            self.selected_paths.remove(entry.path)
            self.selected_entries.pop(entry.path, None)
        else:
            self.selected_paths.add(entry.path)
            self.selected_entries[entry.path] = entry
        self._refresh_selection_state(preserve_cursor=True)

    def action_toggle_select_all(self) -> None:
        """Selects or deselects all files in current directory without moving cursor."""
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
        self._refresh_selection_state(preserve_cursor=True)

    def action_clear_selection(self) -> None:
        """Clears batch selection and resets batch footer bar."""
        self.selected_paths.clear()
        self.selected_entries.clear()
        self._refresh_selection_state(preserve_cursor=True)
        self.query_one(FooterBar).show_toast("Selezione annullata.")

    def _refresh_selection_state(self, preserve_cursor: bool = True) -> None:
        browser = self.query_one(BrowserView)
        browser.update_browser(
            self.current_path,
            self.active_entries,
            self.parent_path,
            self.parent_entries,
            self.selected_paths,
            preserve_cursor=preserve_cursor,
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
        """Downloads selected file(s) to PC or directly transfers them to a second connected Android device."""
        if self.selected_paths:
            entries = list(self.selected_entries.values())
        else:
            entry = self.get_selected_entry()
            if not entry:
                self.query_one(FooterBar).show_toast("Nessun file selezionato per il download", is_error=True)
                return
            entries = [entry]

        def handle_transfer(result: Optional[Tuple[str, str, Optional[AdbDevice]]]) -> None:
            if not result:
                return
            mode, dest_path, target_device = result
            if mode == "pc":
                if len(entries) > 1:
                    self._do_batch_pull_worker(entries, dest_path)
                else:
                    self._do_pull_worker(entries[0].path, dest_path)
            elif mode == "device":
                if target_device:
                    self._do_device_to_device_worker(entries, target_device, dest_path)

        all_devices = self.adb.get_devices()
        self.push_screen(
            DownloadDestinationModal(
                entries=entries,
                default_pc_dir=self.default_pc_download_dir,
                available_devices=all_devices,
                active_device=self.adb.active_device,
            ),
            handle_transfer,
        )

    @work(thread=True)
    def _do_device_to_device_worker(self, entries: List[FileEntry], target_device: AdbDevice, remote_dest_dir: str) -> None:
        import tempfile
        import shutil
        total = len(entries)
        success_count = 0
        batch_tmp_dir = tempfile.mkdtemp(prefix="atui_d2d_")
        source_serial = self.adb.active_device.serial if self.adb.active_device else None

        # Pre-create remote destination folder on target device
        self.adb.run_cmd(["shell", f"mkdir -p '{remote_dest_dir}'"], target_serial=target_device.serial)

        self.app.call_from_thread(
            self.query_one(FooterBar).start_progress,
            float(total),
            t("transfer_d2d_progress", idx=1, total=total, name=entries[0].name, target=target_device.display_name),
        )

        for idx, entry in enumerate(entries, 1):
            self.app.call_from_thread(
                self.query_one(FooterBar).show_toast,
                t("transfer_d2d_progress", idx=idx, total=total, name=entry.name, target=target_device.display_name),
            )
            local_tmp = os.path.join(batch_tmp_dir, entry.name)
            pull_ok, _ = self.adb.pull_file(entry.path, local_tmp, target_serial=source_serial)
            if pull_ok:
                push_ok, _ = self.adb.push_file(local_tmp, remote_dest_dir, target_serial=target_device.serial)
                if push_ok:
                    success_count += 1
                try:
                    if os.path.exists(local_tmp):
                        if os.path.isdir(local_tmp):
                            shutil.rmtree(local_tmp, ignore_errors=True)
                        else:
                            os.remove(local_tmp)
                except Exception:
                    pass
            self.app.call_from_thread(self.query_one(FooterBar).update_progress, 1.0)

        shutil.rmtree(batch_tmp_dir, ignore_errors=True)
        self.app.call_from_thread(self.query_one(FooterBar).finish_progress)
        msg = t("transfer_d2d_complete", count=success_count, total=total, target=target_device.display_name)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, success_count == 0)
        self.selected_paths.clear()
        self.selected_entries.clear()
        self.app.call_from_thread(self._refresh_selection_state)

    @work(thread=True)
    def _do_pull_worker(self, remote_path: str, pc_dest_dir: str) -> None:
        fname = os.path.basename(remote_path)
        self.app.call_from_thread(
            self.query_one(FooterBar).start_progress,
            1.0,
            f"Download in corso: {fname}...",
        )
        success, msg = self.adb.pull_file(remote_path, pc_dest_dir)
        self.app.call_from_thread(self.query_one(FooterBar).update_progress, 1.0)
        self.app.call_from_thread(self.query_one(FooterBar).finish_progress)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)

    @work(thread=True)
    def _do_batch_pull_worker(self, entries: List[FileEntry], pc_dest_dir: str) -> None:
        total = len(entries)
        success_count = 0
        self.app.call_from_thread(
            self.query_one(FooterBar).start_progress,
            float(total),
            f"Download batch (0/{total})...",
        )
        for idx, entry in enumerate(entries, 1):
            self.app.call_from_thread(
                self.query_one(FooterBar).show_toast,
                f"Download batch ({idx}/{total}): {entry.name}...",
            )
            success, _ = self.adb.pull_file(entry.path, pc_dest_dir)
            if success:
                success_count += 1
            self.app.call_from_thread(self.query_one(FooterBar).update_progress, 1.0)

        self.app.call_from_thread(self.query_one(FooterBar).finish_progress)
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
        fname = os.path.basename(pc_file)
        self.app.call_from_thread(
            self.query_one(FooterBar).start_progress,
            1.0,
            f"Caricamento in corso: {fname}...",
        )
        success, msg = self.adb.push_file(pc_file, phone_dest)
        self.app.call_from_thread(self.query_one(FooterBar).update_progress, 1.0)
        self.app.call_from_thread(self.query_one(FooterBar).finish_progress)
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
        if self.selected_paths:
            self.action_delete_batch()
            return

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

    def action_delete_batch(self) -> None:
        """Prompts confirmation and performs batch deletion of all selected items."""
        if not self.selected_paths:
            self.query_one(FooterBar).show_toast("Nessun elemento selezionato per l'eliminazione batch.", is_error=True)
            return

        entries_to_delete = list(self.selected_entries.values())

        def handle_delete_confirm(confirmed: bool) -> None:
            if not confirmed:
                return
            self._do_batch_delete_worker(entries_to_delete)

        self.push_screen(BatchDeleteModal(entries=entries_to_delete), handle_delete_confirm)

    @work(thread=True)
    def _do_batch_delete_worker(self, entries: List[FileEntry]) -> None:
        total = len(entries)
        success_count = 0
        for idx, entry in enumerate(entries, 1):
            self.app.call_from_thread(
                self.query_one(FooterBar).show_toast,
                f"Eliminazione batch ({idx}/{total}): {entry.name}...",
            )
            success, _ = self.adb.delete_entry(entry.path)
            if success:
                success_count += 1

        msg = f"Eliminazione batch completata: {success_count}/{total} elementi rimossi."
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, success_count == 0)
        self.selected_paths.clear()
        self.selected_entries.clear()
        self.load_directory(self.current_path)

    def action_disconnect_device(self) -> None:
        """Disconnects current device and returns to the DisconnectedDashboard."""
        active = self.adb.active_device
        if active:
            dev_name = active.display_name
            self.adb.set_active_device(None)
            self.sync_views()
            self.query_one(FooterBar).show_toast(t("disconnected_toast", name=dev_name))
        else:
            self.sync_views()

    def action_go_main_menu(self) -> None:
        """Navigates to the main menu / dashboard upon clicking AndroidTUI."""
        self.action_disconnect_device()

    def action_quick_jump(self) -> None:
        """Opens quick jump modal for known storage locations (internal, microSD, Downloads, DCIM, Root)."""
        def handle_jump(target_path: Optional[str]) -> None:
            if target_path:
                self.load_directory(target_path)

        self.push_screen(QuickJumpModal(device=self.adb.active_device), handle_jump)

    def action_toggle_language(self) -> None:
        """Toggles interface language between Italian (IT) and English (EN)."""
        new_lang = toggle_language()
        self.query_one(HeaderBar).update_texts()
        self.query_one(FooterBar).update_texts()
        self.query_one(BrowserView).update_texts()
        self.query_one(DisconnectedDashboard).update_texts()
        self.sync_views()
        lang_name = "English (EN)" if new_lang == "en" else "Italiano (IT)"
        self.query_one(FooterBar).show_toast(f"Lingua / Language: {lang_name}")

    def show_no_microsd_toast(self) -> None:
        msg = "Nessuna scheda MicroSD esterna rilevata nel dispositivo." if get_current_language() == "it" else "No external MicroSD card detected in device."
        self.query_one(FooterBar).show_toast(msg, is_error=True)

    # -------------------------------------------------------------
    # Device Management & Mouse Interactions
    # -------------------------------------------------------------
    def action_manage_devices(self) -> None:
        """Opens Device Selection & Addition dialog (USB / WiFi connect / WiFi pair)."""
        devices = self.adb.get_devices()

        def handle_device_select(selected_dev: Any) -> None:
            if not selected_dev:
                return

            if selected_dev == "action:scan_usb":
                self.query_one(FooterBar).show_toast("Scansione dispositivi USB in corso...")
                self.scan_and_auto_connect()
            elif selected_dev == "action:wifi_connect":
                def on_wifi_addr(addr: Optional[str]) -> None:
                    if addr:
                        self._do_wifi_connect_worker(addr)
                self.push_screen(WirelessConnectModal(), on_wifi_addr)
            elif selected_dev == "action:wifi_pair":
                def on_pair_data(data: Optional[tuple]) -> None:
                    if data:
                        addr, code = data
                        self._do_wifi_pair_worker(addr, code)
                self.push_screen(WirelessPairModal(), on_pair_data)
            elif isinstance(selected_dev, AdbDevice):
                self.adb.set_active_device(selected_dev)
                if selected_dev.state == DeviceState.DEVICE:
                    self._on_device_connected(selected_dev)
                else:
                    self._on_device_unready(selected_dev)

        self.push_screen(DeviceSelectModal(devices=devices), handle_device_select)

    def action_select_breadcrumb(self) -> None:
        """Opens interactive breadcrumbs modal to jump to any parent folder/subfolder or custom path."""
        def handle_path(target_path: Optional[str]) -> None:
            if target_path:
                self.load_directory(target_path)

        self.push_screen(PathBreadcrumbsModal(current_path=self.current_path, device=self.adb.active_device), handle_path)

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
        elif btn_id == "fbtn-sort":
            self.action_show_sort_modal()
        elif btn_id == "fbtn-devices":
            self.action_manage_devices()
        elif btn_id == "fbtn-disconnect":
            self.action_disconnect_device()
        elif btn_id == "fbtn-batch-download":
            self.action_download_entry()
        elif btn_id == "fbtn-batch-delete":
            self.action_delete_batch()
        elif btn_id == "fbtn-batch-clear":
            self.action_clear_selection()
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
                    dev_info = remembered[idx]
                    dev_type = dev_info.get("type", "wireless")
                    serial = dev_info.get("serial", "")
                    ip_port = dev_info.get("ip_port", "")
                    name = dev_info.get("name", "Dispositivo")

                    if dev_type == "usb":
                        self.query_one(FooterBar).show_toast(f"Connessione a {name} (USB)...")
                        self.scan_and_auto_connect(preferred_serial=serial)
                    else:
                        target = ip_port or serial
                        if target:
                            self.query_one(FooterBar).show_toast(f"Riconnessione rapida a {name} ({target})...")
                            self._do_wifi_connect_worker(target, select_serial=serial or target)
            except Exception as e:
                self.query_one(FooterBar).show_toast(f"Errore connessione dispositivo: {e}", is_error=True)

        elif btn_id.startswith("btn-del-recent-"):
            try:
                idx = int(btn_id.split("-")[-1])
                remembered = load_remembered_devices()
                if 0 <= idx < len(remembered):
                    target_serial = remembered[idx].get("serial") or remembered[idx].get("ip_port")
                    if target_serial:
                        remove_remembered_device(target_serial)
                        self.query_one(FooterBar).show_toast(t("dash_device_removed"))
                        self.sync_views()
            except Exception as e:
                self.query_one(FooterBar).show_toast(f"Errore rimozione dispositivo: {e}", is_error=True)

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


    @work(thread=True)
    def _do_reconnect_worker(self) -> None:
        success, msg = self.adb.reconnect_devices()
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)
        self.scan_and_auto_connect()

    @work(thread=True)
    def _do_wifi_connect_worker(self, addr: str, select_serial: Optional[str] = None) -> None:
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, f"Connessione a {addr}...")
        success, msg = self.adb.wireless_connect(addr)
        self.app.call_from_thread(self.query_one(FooterBar).show_toast, msg, not success)
        self.scan_and_auto_connect(preferred_serial=select_serial or addr)

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
        import tempfile, shutil
        try:
            cache_dir = Path(tempfile.gettempdir()) / "atui_preview_cache"
            if cache_dir.exists():
                shutil.rmtree(cache_dir, ignore_errors=True)
        except Exception:
            pass
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
                sdcard_path="/sdcard",
                ext_sd_path="/storage/1F2A-3B4C",
                ext_sd_free="112 GB",
                ext_sd_total="128 GB",
            )
        )

    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)

