"""
Browser view component with 3-Pane Miller Columns inspired by pikpaktui.
- Left Pane: Parent Directory (Ancestor context)
- Middle Pane: Current Directory (Interactive file list)
- Right Pane: File Preview and Metadata Pane
"""
from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Static, DataTable, ListView, ListItem, Label
from rich.text import Text
from rich.markup import escape

from ..models import FileEntry, FileCategory
from ..theme import get_icon, get_color, is_text_previewable


class BrowserView(Container):
    """Miller columns 3-pane file manager view."""

    def __init__(self, **kwargs):
        super().__init__(id="miller-container", **kwargs)
        self.current_path: str = "/sdcard"
        self.parent_path: str = "/"
        self.current_entries: List[FileEntry] = []
        self.parent_entries: List[FileEntry] = []
        self.selected_entry: Optional[FileEntry] = None

    def compose(self) -> ComposeResult:
        # Left Pane: Parent Directory
        with Vertical(id="parent-pane", classes="pane"):
            yield Static(" 📁 Genitore ", id="parent-pane-title", classes="meta-key")
            yield ListView(id="parent-list")

        # Middle Pane: Current Directory
        with Vertical(id="current-pane", classes="pane"):
            yield Static(" 📂 Contenuto: /sdcard ", id="current-pane-title", classes="meta-key")
            yield DataTable(id="current-table", cursor_type="row")

        # Right Pane: Preview Pane
        with Vertical(id="preview-pane", classes="pane"):
            yield Static(" 📄 Anteprima & Dettagli ", id="preview-pane-title", classes="meta-key")
            with VerticalScroll(id="preview-scroll"):
                yield Static(id="preview-image")
                yield Static("Nessun elemento selezionato.", id="preview-body")

    def on_mount(self) -> None:
        table = self.query_one("#current-table", DataTable)
        table.add_columns("Nome", "Dimensione", "Modificato", "Permessi")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Mouse click on parent directory item navigates to parent directory."""
        self.app.action_go_parent()

    def update_browser(
        self,
        current_path: str,
        current_entries: List[FileEntry],
        parent_path: str,
        parent_entries: List[FileEntry],
        selected_paths: Optional[set] = None,
    ) -> None:
        self.current_path = current_path
        self.current_entries = current_entries
        self.parent_path = parent_path
        self.parent_entries = parent_entries
        selected_set = selected_paths or set()

        # Update Titles
        self.query_one("#current-pane-title", Static).update(f" 📂 Contenuto: {current_path} ({len(current_entries)}) ")
        self.query_one("#parent-pane-title", Static).update(f" 📁 Genitore: {parent_path} (Clicca per salire) ")

        # Update Parent List (Left Pane)
        parent_list = self.query_one("#parent-list", ListView)
        parent_list.clear()
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
        table = self.query_one("#current-table", DataTable)
        table.clear()

        for entry in current_entries:
            icon = get_icon(entry.category)
            color = get_color(entry.category)

            # Styled Name with selection checkbox indicator
            name_text = Text()
            if entry.path in selected_set:
                name_text.append("[✓] ", style="bold #73daca")
            else:
                name_text.append("[ ] ", style="dim #565f89")

            name_text.append(f"{icon} ", style=color)
            name_text.append(entry.name, style=f"bold {color}" if entry.is_dir else color)

            # Styled Size
            size_style = "#7aa2f7" if entry.is_dir else "#9aa5ce"
            size_text = Text(entry.formatted_size, style=size_style)

            # Date & Perms
            date_text = Text(entry.date_str or "—", style="#565f89")
            perms_text = Text(entry.permissions or "—", style="#414868")

            table.add_row(name_text, size_text, date_text, perms_text, key=entry.path)

        if current_entries:
            table.move_cursor(row=0)
            self.set_selected_entry(current_entries[0])
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
            preview_body.update("[dim]Cartella vuota o nessun elemento selezionato.[/]")
            return

        icon = get_icon(entry.category)
        color = get_color(entry.category)

        # Handle Image Preview Pane
        if entry.category == FileCategory.IMAGE:
            preview_img.display = True
            if image_render is not None:
                preview_img.update(image_render)
            else:
                preview_img.update("[dim #bb9af7]🖼️  Caricamento anteprima dal telefono...[/]")
        else:
            preview_img.update("")
            preview_img.display = False

        # Build formatted details
        markup = []
        safe_name = escape(entry.name)
        safe_path = escape(entry.path)
        markup.append(f"[{color} bold]{icon} {safe_name}[/]")
        markup.append(f"[dim]{safe_path}[/]\n")

        markup.append(f"[bold #7dcfff]Tipo:[/] {entry.category.value.capitalize()}")
        markup.append(
            f"[bold #7dcfff]Dimensione:[/] {entry.formatted_size} ({entry.size:,} byte)"
            if not entry.is_dir
            else "[bold #7dcfff]Tipo:[/] Cartella di sistema/utente"
        )
        markup.append(f"[bold #7dcfff]Permessi:[/] [dim]{escape(entry.permissions or 'sconosciuti')}[/]")
        markup.append(f"[bold #7dcfff]Data:[/] [dim]{escape(entry.date_str or 'sconosciuta')}[/]")

        if entry.is_symlink:
            markup.append(f"[bold #e0af68]Collegamento simbolico ->[/] {escape(entry.link_target)}")

        markup.append("\n" + "─" * 28 + "\n")

        if entry.is_dir:
            markup.append("[#73daca]Premi [bold]\\[Enter][/] o doppio click per esplorare questa cartella.[/]")
        else:
            markup.append("[bold #7aa2f7]Dettagli Contenuto:[/\n]")
            if entry.category == FileCategory.IMAGE:
                markup.append("[#bb9af7]🖼️  Immagine visualizzata in anteprima sopra[/]")
                markup.append(f"[#c0caf5]Formato:[/] [bold #7dcfff]{entry.extension.upper() or 'IMG'}[/]")
                if image_dim:
                    markup.append(f"[#c0caf5]Risoluzione:[/] [bold #73daca]{image_dim}[/]")
                markup.append("[bold #73daca]Premi \\[d\\] per scaricare il file originale sul PC.[/]")
            elif entry.category == FileCategory.VIDEO:
                markup.append("[#b4f9f8]🎬 File Video[/]")
                markup.append(f"[#c0caf5]Formato:[/] [bold #7dcfff]{entry.extension.upper() or 'VIDEO'}[/]")
                markup.append(f"[#c0caf5]Dimensione:[/] {entry.formatted_size}")
                markup.append("[bold #73daca]Premi \\[d\\] per scaricare il video sul PC.[/]")
            elif entry.category == FileCategory.AUDIO:
                markup.append("[#7aa2f7]🎵 File Audio / Musica[/]")
                markup.append(f"[#c0caf5]Formato:[/] [bold #7dcfff]{entry.extension.upper() or 'AUDIO'}[/]")
                markup.append(f"[#c0caf5]Dimensione:[/] {entry.formatted_size}")
                markup.append("[bold #73daca]Premi \\[d\\] per scaricare il brano sul PC.[/]")
            elif entry.category == FileCategory.APK:
                markup.append("[#9ece6a]🤖 Pacchetto Applicazione Android (APK)[/]")
                markup.append(f"[#c0caf5]Nome:[/] [bold #7dcfff]{safe_name}[/]")
                markup.append(f"[#c0caf5]Dimensione:[/] {entry.formatted_size}")
                markup.append("[bold #73daca]Premi \\[d\\] per scaricare l'APK sul PC.[/]")
            elif entry.category == FileCategory.ARCHIVE:
                markup.append("[#ff9e64]📦 Archivio Compresso[/]")
                markup.append(f"[#c0caf5]Formato:[/] [bold #7dcfff]{entry.extension.upper() or 'ARCHIVIO'}[/]")
                markup.append(f"[#c0caf5]Dimensione:[/] {entry.formatted_size}")
                markup.append("[bold #73daca]Premi \\[d\\] per scaricare l'archivio sul PC.[/]")
            elif is_text_previewable(entry.name, entry.is_dir):
                if preview_text:
                    escaped_preview = escape(preview_text[:2000])
                    markup.append(f"[#c0caf5]{escaped_preview}[/]")
                else:
                    markup.append("[dim]Caricamento anteprima testo in corso...[/]")
            else:
                markup.append(f"[dim]File binario {entry.extension.upper() or ''} (nessuna anteprima testuale).[/]")
                markup.append("[bold #73daca]Premi \\[d\\] per scaricare il file sul PC.[/]")

        markup.append("\n" + "─" * 28 + "\n")
        markup.append("[bold #7dcfff]Azioni rapide & Mouse:[/\n]")
        markup.append(" • [bold #73daca]\\[d][/] Scarica sul PC")
        markup.append(" • [bold #73daca]\\[␣ Spazio][/] Seleziona per download batch")
        markup.append(" • [bold #e0af68]\\[n][/] Rinomina file")
        markup.append(" • [bold #f7768e]\\[x][/] Elimina dal telefono")

        preview_body.update("\n".join(markup))

