"""DocNotes main window — three-panel layout with notebook tree, note list, and editor."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter, QAction,
    QInputDialog, QMessageBox, QShortcut, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

from docnotes.config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT
from docnotes.core.vault import Vault
from docnotes.core.notebook import Notebook, Section, Page
from docnotes.ui.notebook_tree import NotebookTree
from docnotes.ui.note_list import NoteList
from docnotes.ui.note_editor import NoteEditor
from docnotes.ui.sticky_panel import DocNotesStickyManager


class MainWindow(QMainWindow):
    def __init__(self, vault: Vault, app_instance=None):
        super().__init__()
        self._vault = vault
        self._app = app_instance
        self._active_notebook: Notebook | None = None
        self._active_section: Section | None = None
        self._sticky_manager: DocNotesStickyManager | None = None

        self._setup_window()
        self._setup_menu()
        self._setup_panels()
        self._setup_shortcuts()
        self._load_vault()
        self._setup_stickies()

    def _setup_window(self):
        self.setWindowTitle(APP_NAME)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.setAcceptDrops(True)

    def _setup_menu(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("New &Notebook...", self._new_notebook, QKeySequence("Ctrl+Shift+N"))
        file_menu.addAction("New &Section...", self._new_section)
        file_menu.addAction("New &Page", self._new_page, QKeySequence("Ctrl+N"))
        file_menu.addSeparator()
        file_menu.addAction("New Sticky Note", self.create_sticky, QKeySequence("Ctrl+Alt+N"))
        file_menu.addSeparator()
        file_menu.addAction("&Import OneNote...", self._import_onenote)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.close, QKeySequence("Ctrl+Q"))

        # Edit
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction("&Search All Notes...", self._search_notes, QKeySequence("Ctrl+Shift+F"))

        # View
        view_menu = menubar.addMenu("&View")
        view_menu.addAction("Show All Stickies", self._show_all_stickies)
        view_menu.addAction("Hide All Stickies", self._hide_all_stickies)
        view_menu.addSeparator()
        view_menu.addAction("Refresh", self._refresh_vault, QKeySequence("F5"))

        # Help
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&About", self._show_about)

    def _setup_panels(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left: Notebook tree
        self._tree = NotebookTree()
        self._tree.section_selected.connect(self._on_section_selected)
        self._tree.notebook_selected.connect(self._on_notebook_selected)
        self._tree.create_notebook_requested.connect(self._new_notebook)
        self._tree.create_section_requested.connect(self._new_section_in)
        self._tree.sticky_requested.connect(self.create_sticky)
        self._tree.delete_notebook_requested.connect(self._delete_notebook)
        self._tree.delete_section_requested.connect(self._delete_section)
        splitter.addWidget(self._tree)

        # Center-left: Note list
        self._note_list = NoteList()
        self._note_list.note_selected.connect(self._on_note_selected)
        self._note_list.new_page_requested.connect(self._new_page)
        self._note_list.sticky_requested.connect(self._new_sticky_for_current_section)
        self._note_list.delete_page_requested.connect(self._delete_page)
        self._note_list.pin_toggled.connect(self._toggle_pin)
        splitter.addWidget(self._note_list)

        # Center-right: Note editor
        self._editor = NoteEditor()
        self._editor.content_saved.connect(self._on_content_saved)
        self._editor.wikilink_clicked.connect(self._on_wikilink_clicked)
        splitter.addWidget(self._editor)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 0)
        splitter.setStretchFactor(2, 1)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Escape"), self, self._on_escape)

    def _setup_stickies(self):
        sections = self._get_all_section_paths()
        self._sticky_manager = DocNotesStickyManager(self._vault.root, sections)
        self._sticky_manager.load_all()

    def _get_all_section_paths(self) -> list[str]:
        paths = []
        for nb in self._vault.notebooks:
            for sec in nb.sections:
                paths.append(f"{nb.name}/{sec.name}")
        return paths

    # ── Vault loading ──

    def _load_vault(self):
        self._vault.scan()
        self._tree.load_vault(self._vault.notebooks)

    def _refresh_vault(self):
        self._vault.scan()
        self._tree.load_vault(self._vault.notebooks)
        if self._sticky_manager:
            self._sticky_manager.update_sections(self._get_all_section_paths())

    # ── Section/Note selection ──

    def _on_notebook_selected(self, notebook: Notebook):
        self._active_notebook = notebook
        self._active_section = None
        self._note_list.clear_list()
        self._editor.clear()

    def _on_section_selected(self, notebook: Notebook, section: Section):
        self._active_notebook = notebook
        self._active_section = section

        # Include sticky notes assigned to this section
        section_path = f"{notebook.name}/{section.name}"
        pages = list(section.pages)

        # Add stickies assigned to this section
        for sticky in self._vault.get_all_stickies():
            try:
                text = sticky.path.read_text(encoding='utf-8', errors='replace')
                from app.core.obsidian.frontmatter import parse_frontmatter
                fm, _ = parse_frontmatter(text)
                if fm.get('section', '') == section_path:
                    pages.append(sticky)
            except OSError:
                pass

        self._note_list.load_pages(section.name, pages)
        self._editor.clear()

    def _on_note_selected(self, page: Page):
        self._editor.load_note(page)

    def _on_content_saved(self):
        # Refresh the note list to update timestamps
        if self._active_section and self._active_notebook:
            self._vault.scan()
            self._on_section_selected(self._active_notebook, self._active_section)

    # ── CRUD ──

    def _new_notebook(self):
        name, ok = QInputDialog.getText(self, "New Notebook", "Notebook name:")
        if ok and name.strip():
            self._vault.create_notebook(name.strip())
            self._refresh_vault()

    def _new_section(self):
        if not self._active_notebook:
            QMessageBox.information(self, "Info", "Select a notebook first.")
            return
        self._new_section_in(self._active_notebook)

    def _new_section_in(self, notebook: Notebook):
        name, ok = QInputDialog.getText(self, "New Section", "Section name:")
        if ok and name.strip():
            self._vault.create_section(notebook, name.strip())
            self._refresh_vault()

    def _new_page(self):
        if not self._active_section:
            QMessageBox.information(self, "Info", "Select a section first.")
            return
        title, ok = QInputDialog.getText(self, "New Page", "Page title:")
        if ok and title.strip():
            page = self._vault.create_page(self._active_section, title.strip())
            self._refresh_vault()
            if self._active_notebook and self._active_section:
                self._on_section_selected(self._active_notebook, self._active_section)
            self._editor.load_note(page)

    def _delete_notebook(self, notebook: Notebook):
        result = QMessageBox.question(
            self, "Delete Notebook",
            f"Delete notebook '{notebook.name}' and all its contents?",
            QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            self._vault.delete_notebook(notebook)
            self._refresh_vault()
            self._note_list.clear_list()
            self._editor.clear()

    def _delete_section(self, notebook: Notebook, section: Section):
        result = QMessageBox.question(
            self, "Delete Section",
            f"Delete section '{section.name}' and all its pages?",
            QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            self._vault.delete_section(notebook, section)
            self._refresh_vault()
            self._note_list.clear_list()
            self._editor.clear()

    def _delete_page(self, page: Page):
        result = QMessageBox.question(
            self, "Delete Page",
            f"Delete '{page.name}'?",
            QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            if self._active_section:
                self._vault.delete_page(self._active_section, page)
                self._on_section_selected(self._active_notebook, self._active_section)
            self._editor.clear()

    def _toggle_pin(self, page: Page):
        from docnotes.core.note_document import NoteDocument
        doc = NoteDocument()
        doc.open(str(page.path))
        doc.pinned = not page.pinned
        doc.save()
        if self._active_notebook and self._active_section:
            self._vault.scan()
            self._on_section_selected(self._active_notebook, self._active_section)

    # ── Sticky notes ──

    def create_sticky(self, section: str = ""):
        if self._sticky_manager:
            self._sticky_manager.create_note(section=section)

    def _new_sticky_for_current_section(self):
        section_path = ""
        if self._active_notebook and self._active_section:
            section_path = f"{self._active_notebook.name}/{self._active_section.name}"
        self.create_sticky(section=section_path)

    def _show_all_stickies(self):
        if self._sticky_manager:
            self._sticky_manager.show_all()

    def _hide_all_stickies(self):
        if self._sticky_manager:
            self._sticky_manager.hide_all()

    # ── Search ──

    def _search_notes(self):
        query, ok = QInputDialog.getText(self, "Search Notes", "Search:")
        if ok and query.strip():
            results = self._vault.search_pages(query.strip())
            if not results:
                QMessageBox.information(self, "Search", "No results found.")
                return
            # Show results in note list
            self._note_list.load_pages(f"Search: {query}", results)

    # ── Wikilinks ──

    def _on_wikilink_clicked(self, target: str):
        results = self._vault.search_pages(target)
        if results:
            self._editor.load_note(results[0])

    # ── Import ──

    def _import_onenote(self):
        path = QFileDialog.getExistingDirectory(self, "Select exported OneNote folder")
        if not path:
            return
        try:
            from docnotes.core.onenote_import import import_onenote_folder
            count = import_onenote_folder(path, self._vault)
            QMessageBox.information(self, "Import", f"Imported {count} pages.")
            self._refresh_vault()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    # ── Misc ──

    def _on_escape(self):
        pass

    def _show_about(self):
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h2>{APP_NAME} v{APP_VERSION}</h2>"
            f"<p>Note-taking with Vault/Notebook/Section/Page hierarchy</p>"
            f"<p>Built by Operator Systems // BLACK TECH WIZARD</p>"
        )

    def closeEvent(self, event):
        event.accept()
