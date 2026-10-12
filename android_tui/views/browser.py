"""
Miller Columns Browser View for AndroidTUI.
Presents the file hierarchy in 3 dynamic panes:
1. Parent Directory (with cursor-selectable go-up navigation item)
2. Current Directory (with mouse-clickable checkbox squares and sortable headers)
3. Preview Pane (high-res images, video frames, category graphic cards, and text previews)
"""
from typing import List, Optional
from rich.text import Text
from rich.markup import escape

from textual import events
from textual.message import Message
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, DataTable, ListView, ListItem, Label

from ..models import FileEntry, FileCategory
from ..theme import get_icon, get_color, is_text_previewable
from ..i18n import t


class FileTable(DataTable):
    """Custom DataTable that intercepts mouse clicks on the checkbox column, header sort, and double clicks."""

    class CheckboxToggled(Message):
        """Posted when a user clicks on the checkbox square of a specific row."""
        def __init__(self, row_index: int, row_key: str):
            super().__init__()
            self.row_index = row_index
            self.row_key = row_key

    class SelectAllToggled(Message):
        """Posted when a user clicks the checkbox column header."""
        pass

    class FileDoubleClicked(Message):
        """Posted when a user double clicks on a file or folder row."""
        def __init__(self, row_index: int):
            super().__init__()
            self.row_index = row_index

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_click_time = 0.0
        self._last_click_row = -1

    async def _on_click(self, event: events.Click) -> None:
        meta = event.style.meta
        col_idx = meta.get("column")
        row_idx = meta.get("row")

        # Column 0 is the dedicated interactive checkbox column
        if col_idx == 0:
            if row_idx is not None and row_idx >= 0:
                row_key = ""
                if row_idx < len(self.ordered_rows):
                    row_key = str(self.ordered_rows[row_idx].key.value)
                self.post_message(self.CheckboxToggled(row_index=row_idx, row_key=row_key))
                event.stop()
                return
            elif row_idx == -1:
                self.post_message(self.SelectAllToggled())
                event.stop()
                return

        # Header clicks on columns: Sort by Name, Size, Type, Date, Perms
        if row_idx == -1:
            if col_idx == 1 and hasattr(self.app, "sort_directory"):
                self.app.sort_directory("name")
                event.stop()
                return
            elif col_idx == 2 and hasattr(self.app, "sort_directory"):
                self.app.sort_directory("size")
                event.stop()
                return
            elif col_idx == 3 and hasattr(self.app, "sort_directory"):
                self.app.sort_directory("type")
                event.stop()
                return
            elif col_idx == 4 and hasattr(self.app, "sort_directory"):
                self.app.sort_directory("modified")
                event.stop()
                return
            elif col_idx == 5 and hasattr(self.app, "sort_directory"):
                self.app.sort_directory("perms")
                event.stop()
                return
            await super()._on_click(event)
            return

        # Data rows: Single click highlights & previews, Double click opens!
        if row_idx is not None and row_idx >= 0:
            import time
            from textual.coordinate import Coordinate
            now = time.time()
            is_double = (now - self._last_click_time < 0.45) and (row_idx == self._last_click_row)
            self._last_click_time = now
            self._last_click_row = row_idx

            # Update cursor position to trigger RowHighlighted & live preview
            self.cursor_coordinate = Coordinate(row_idx, col_idx if col_idx is not None else 1)

            if is_double:
                self.post_message(self.FileDoubleClicked(row_index=row_idx))
            event.stop()
            return

        await super()._on_click(event)


class BrowserView(Horizontal):
    """3-column Miller columns file manager with rich previews and keyboard navigation."""

    def __init__(self, **kwargs):
        super().__init__(id="miller-container", **kwargs)
        self.current_entries: List[FileEntry] = []
        self.parent_entries: List[FileEntry] = []
        self.selected_entry: Optional[FileEntry] = None
        self.current_path: str = "/sdcard"
        self.parent_path: str = "/"
        self.selected_paths: set = set()
        self.sort_by: str = "name"
        self.sort_reverse: bool = False
        self.col_widths: dict = {
            "sel": 5,
            "name": 34,
            "size": 12,
            "type": 12,
            "modified": 18,
            "perms": 12,
        }

    def compose(self) -> ComposeResult:
        # Left Pane: Parent Directory
        with Vertical(id="parent-pane", classes="pane"):
            yield Static(t("parent_pane_title", path="/"), id="parent-pane-title", classes="meta-key")
            yield ListView(id="parent-list")

        # Middle Pane: Current Directory with FileTable
        with Vertical(id="current-pane", classes="pane"):
            yield Static(t("current_pane_title", path="/sdcard", count=0), id="current-pane-title", classes="meta-key")
            yield FileTable(id="current-table", cursor_type="row")

        # Right Pane: Preview Pane
        with Vertical(id="preview-pane", classes="pane"):
            yield Static(t("preview_pane_title"), id="preview-pane-title", classes="meta-key")
            with VerticalScroll(id="preview-scroll"):
                yield Static(id="preview-image")
                yield Static(t("empty_folder"), id="preview-body")

    def _get_column_labels(self, sort_by: str = "name", sort_reverse: bool = False) -> list:
        arrow = " ▼" if sort_reverse else " ▲"
        name_lbl = t("col_name") + (arrow if sort_by == "name" else "")
        size_lbl = t("col_size") + (arrow if sort_by == "size" else "")
        type_lbl = t("col_type") + (arrow if sort_by == "type" else "")
        mod_lbl = t("col_modified") + (arrow if sort_by in ("modified", "date") else "")
        perms_lbl = t("col_perms") + (arrow if sort_by in ("perms", "permissions") else "")
        return [
            (t("col_sel"), self.col_widths.get("sel", 5)),
            (name_lbl, self.col_widths.get("name", 34)),
            (size_lbl, self.col_widths.get("size", 12)),
            (type_lbl, self.col_widths.get("type", 12)),
            (mod_lbl, self.col_widths.get("modified", 18)),
            (perms_lbl, self.col_widths.get("perms", 12)),
        ]

    def on_mount(self) -> None:
        table = self.query_one("#current-table", FileTable)
        for label, width in self._get_column_labels(self.sort_by, self.sort_reverse):
            table.add_column(label, width=width)

    def update_columns(self, sort_by: str = "name", sort_reverse: bool = False, col_widths: Optional[dict] = None) -> None:
        """Updates column headers with sort arrow indicators and explicit column widths."""
        self.sort_by = sort_by
        self.sort_reverse = sort_reverse
        if col_widths:
            self.col_widths.update(col_widths)
        table = self.query_one("#current-table", FileTable)
        table.clear(columns=True)
        for label, width in self._get_column_labels(sort_by, sort_reverse):
            table.add_column(label, width=width)
        self.update_browser(
            self.current_path,
            self.current_entries,
            self.parent_path,
            self.parent_entries,
            self.selected_paths,
            preserve_cursor=True,
        )

    def update_texts(self) -> None:
        """Refreshes localized labels and column headers when language changes."""
        self.query_one("#preview-pane-title", Static).update(t("preview_pane_title"))
        self.update_columns(self.sort_by, self.sort_reverse)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Cursor selection (Enter) or mouse click in the parent list pane."""
        if event.list_view.id == "parent-list":
            idx = event.list_view.index
            if idx == 0:
                # User selected "⬆️ .. [Salire alla cartella genitore]"!
                self.app.action_go_parent()
            elif idx is not None and 1 <= idx <= len(self.parent_entries):
                # User selected a sibling directory!
                target_folder = self.parent_entries[idx - 1]
                if target_folder.is_dir or target_folder.is_symlink:
                    self.app.load_directory(target_folder.path)

    def on_click(self, event) -> None:
        """Clicking on parent pane title ascends; clicking current pane title opens breadcrumbs."""
        widget = event.widget
        if widget and widget.id == "parent-pane-title":
            self.app.action_go_parent()
        elif widget and widget.id == "current-pane-title":
            self.app.action_select_breadcrumb()

    def update_browser(
        self,
        current_path: str,
        current_entries: List[FileEntry],
        parent_path: str,
        parent_entries: List[FileEntry],
        selected_paths: Optional[set] = None,
        preserve_cursor: bool = False,
    ) -> None:
        self.current_path = current_path
        self.current_entries = current_entries
        self.parent_path = parent_path
        self.parent_entries = parent_entries
        selected_set = selected_paths or set()
        self.selected_paths = selected_set

        # Update Titles
        self.query_one("#current-pane-title", Static).update(
            t("current_pane_title", path=current_path, count=len(current_entries))
        )
        self.query_one("#parent-pane-title", Static).update(
            t("parent_pane_title", path=parent_path)
        )

        # Update Parent List (Left Pane)
        parent_list = self.query_one("#parent-list", ListView)
        parent_list.clear()

        # Item 0: Go up to parent folder (Selectable with keyboard cursor and clickable!)
        up_text = Text()
        up_text.append("⬆️ .. ", style="bold #e0af68")
        up_text.append(t("parent_go_up_item"), style="bold #7dcfff")
        parent_list.append(ListItem(Label(up_text)))

        # Sibling folders start at index 1
        current_folder_name = current_path.rstrip("/").split("/")[-1]
        for p_entry in parent_entries:
            icon = get_icon(p_entry.category)
            color = get_color(p_entry.category)
            label_text = Text()
            label_text.append(f"{icon} ", style=color)
            if p_entry.name == current_folder_name:
                label_text.append(p_entry.name, style=f"bold {color} underline")
            else:
                label_text.append(p_entry.name, style="dim #c0caf5")
            parent_list.append(ListItem(Label(label_text)))

        # Update Current Directory Table (Middle Pane)
        table = self.query_one("#current-table", FileTable)
        saved_row = table.cursor_row if preserve_cursor else 0
        table.clear()

        for entry in current_entries:
            icon = get_icon(entry.category)
            color = get_color(entry.category)

            # Col 0: Dedicated clickable checkbox square
            if entry.path in selected_set:
                sel_text = Text("[✓]", style="bold #73daca")
            else:
                sel_text = Text("[ ]", style="dim #565f89")

            # Col 1: Icon and file name
            name_text = Text()
            name_text.append(f"{icon} ", style=color)
            name_text.append(entry.name, style=f"bold {color}" if entry.is_dir else color)

            # Col 2: Size
            size_style = "#7aa2f7" if entry.is_dir else "#9aa5ce"
            size_text = Text(entry.formatted_size, style=size_style)

            # Col 3: Type / Category
            cat_label = t(f"cat_{entry.category.value}")
            type_text = Text(cat_label, style=color)

            # Col 4: Date
            date_text = Text(entry.date_str or "—", style="#565f89")

            # Col 5: Perms
            perms_text = Text(entry.permissions or "—", style="#414868")

            table.add_row(sel_text, name_text, size_text, type_text, date_text, perms_text, key=entry.path)

        if current_entries:
            target_row = max(0, min(saved_row, len(current_entries) - 1))
            table.move_cursor(row=target_row)
            self.set_selected_entry(current_entries[target_row])
        else:
            self.set_selected_entry(None)

    def set_selected_entry(
        self,
        entry: Optional[FileEntry],
        preview_text: Optional[str] = None,
        image_render: Optional[Text] = None,
        image_dim: Optional[str] = None,
    ) -> None:
        self.selected_entry = entry
        preview_img = self.query_one("#preview-image", Static)
        preview_body = self.query_one("#preview-body", Static)

        if not entry:
            preview_img.update("")
            preview_img.display = False
            preview_body.update(f"[dim]{t('empty_folder')}[/]")
            return

        icon = get_icon(entry.category)
        color = get_color(entry.category)

        # Handle Thumbnail Graphic / Card Display for ALL file categories
        preview_img.display = True
        if image_render is not None:
            preview_img.update(image_render)
        else:
            loading_msg = f"{icon} {t('preview_loading')}"
            preview_img.update(f"[dim #bb9af7]{loading_msg}[/]")

        # Build formatted details
        markup = []
        safe_name = escape(entry.name)
        safe_path = escape(entry.path)
        markup.append(f"[{color} bold]{icon} {safe_name}[/]")
        markup.append(f"[dim]{safe_path}[/]\n")

        cat_desc = t(f"cat_{entry.category.value}")
        markup.append(f"[bold #7dcfff]{t('meta_type')}:[/] {cat_desc}")
        markup.append(
            f"[bold #7dcfff]{t('meta_size')}:[/] {entry.formatted_size} ({entry.size:,} byte)"
            if not entry.is_dir
            else f"[bold #7dcfff]{t('meta_type')}:[/] {t('meta_folder_desc')}"
        )
        markup.append(f"[bold #7dcfff]{t('meta_perms')}:[/] [dim]{escape(entry.permissions or '—')}[/]")
        markup.append(f"[bold #7dcfff]{t('meta_date')}:[/] [dim]{escape(entry.date_str or '—')}[/]")

        if entry.is_symlink:
            markup.append(f"[bold #e0af68]Link ->[/] {escape(entry.link_target)}")

        markup.append("\n" + "─" * 28 + "\n")

        if entry.is_dir:
            markup.append(f"[#73daca]{t('meta_enter_folder_hint')}[/]")
        else:
            markup.append(f"[bold #7aa2f7]{t('meta_content_details')}:[/\n]")
            if entry.category == FileCategory.IMAGE:
                img_lbl = t("meta_img_preview_raylib") if (image_dim and "Raylib-Go" in image_dim) else t("meta_img_preview")
                markup.append(f"[#bb9af7]{img_lbl}[/]")
                markup.append(f"[#c0caf5]{t('meta_format')}:[/] [bold #7dcfff]{entry.extension.upper() or 'IMG'}[/]")
                if image_dim:
                    markup.append(f"[#c0caf5]{t('meta_resolution')}:[/] [bold #73daca]{image_dim}[/]")
                markup.append(f"[bold #73daca]{t('meta_press_d_dl')}[/]")
            elif entry.category == FileCategory.VIDEO:
                markup.append(f"[#b4f9f8]{t('meta_vid_preview')}[/]")
                markup.append(f"[#c0caf5]{t('meta_format')}:[/] [bold #7dcfff]{entry.extension.upper() or 'VIDEO'}[/]")
                if image_dim:
                    markup.append(f"[#c0caf5]{t('meta_resolution')}:[/] [bold #73daca]{image_dim}[/]")
                markup.append(f"[#c0caf5]{t('meta_size')}:[/] {entry.formatted_size}")
                markup.append(f"[bold #73daca]{t('meta_press_d_dl')}[/]")

            elif entry.category == FileCategory.AUDIO:
                markup.append(f"[#7aa2f7]{t('meta_audio_desc')}[/]")
                markup.append(f"[#c0caf5]{t('meta_format')}:[/] [bold #7dcfff]{entry.extension.upper() or 'AUDIO'}[/]")
                markup.append(f"[#c0caf5]{t('meta_size')}:[/] {entry.formatted_size}")
                markup.append(f"[bold #73daca]{t('meta_press_d_dl')}[/]")
            elif entry.category == FileCategory.APK:
                markup.append(f"[#9ece6a]{t('meta_apk_desc')}[/]")
                markup.append(f"[#c0caf5]{t('meta_size')}:[/] {entry.formatted_size}")
                markup.append(f"[bold #73daca]{t('meta_press_d_dl')}[/]")
            elif entry.category == FileCategory.ARCHIVE:
                markup.append(f"[#ff9e64]{t('meta_archive_desc')}[/]")
                markup.append(f"[#c0caf5]{t('meta_format')}:[/] [bold #7dcfff]{entry.extension.upper() or 'ARCHIVE'}[/]")
                markup.append(f"[#c0caf5]{t('meta_size')}:[/] {entry.formatted_size}")
                markup.append(f"[bold #73daca]{t('meta_press_d_dl')}[/]")
            elif is_text_previewable(entry.name, entry.is_dir):
                if preview_text:
                    escaped_preview = escape(preview_text[:2000])
                    markup.append(f"[#c0caf5]{escaped_preview}[/]")
                else:
                    markup.append(f"[dim]{t('preview_loading_text')}[/]")
            else:
                markup.append(f"[dim]{t('meta_generic_binary', ext=entry.extension.upper() or 'DATA')}[/]")
                markup.append(f"[bold #73daca]{t('meta_press_d_dl')}[/]")

        markup.append("\n" + "─" * 28 + "\n")
        markup.append(f"[bold #7dcfff]{t('meta_quick_actions')}[/]")
        markup.append(t("meta_act_open"))
        markup.append(t("meta_act_dl"))
        markup.append(t("meta_act_upload"))
        markup.append(t("meta_act_select"))
        markup.append(t("meta_act_path"))
        markup.append(t("meta_act_sort"))
        markup.append(t("meta_act_rename"))
        markup.append(t("meta_act_delete"))

        preview_body.update("\n".join(markup))
