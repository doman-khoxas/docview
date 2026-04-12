"""Main application window with tabs, sidebar, viewport, toolbar, and editor."""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QFileDialog,
    QMessageBox, QAction, QShortcut, QDockWidget, QSplitter, QHBoxLayout
)
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QKeySequence
from pathlib import Path

from app.version import APP_NAME
from app.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT,
    WINDOW_TITLE, PDF_EXTENSIONS, MARKDOWN_EXTENSIONS
)
from app.document_manager import DocumentManager
from app.recent_files import RecentFiles
from app.ui.tab_bar import DocTabBar
from app.ui.toolbar import DocToolbar
from app.ui.status_bar import DocStatusBar
from app.ui.welcome_screen import WelcomeScreen
from app.ui.viewport.pdf_viewport import PDFViewport
from app.ui.properties_panel import PropertiesPanel
from app.ui.search_panel import SearchPanel
from app.ui.sidebar.sidebar_panel import SidebarPanel
from app.ui.context_menu import ViewportContextMenu
from app.ui.editor.editor_widget import EditorWidget


class MainWindow(QMainWindow):
    def __init__(self, app_instance=None):
        super().__init__()
        self._app_instance = app_instance
        self.doc_manager = DocumentManager()
        self.recent_files = RecentFiles()
        self.active_tool = None
        self._tool_instances: dict[str, object] = {}
        self._sticky_manager = None
        self._form_field_manager = None
        self._form_field_overlay = None
        self._form_fields_visible = False

        self._setup_window()
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central()
        self._setup_status_bar()
        self._setup_shortcuts()
        self._load_vault_config()
        self._setup_sticky_notes()
        self._show_welcome()

    def _setup_window(self):
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.setAcceptDrops(True)

    def _setup_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        close_tab_action = QAction("&Close Tab", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(lambda: self.close_tab(self.doc_manager.active_index))
        file_menu.addAction(close_tab_action)
        file_menu.addSeparator()
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        self._undo_action = QAction("&Undo", self)
        self._undo_action.setShortcut(QKeySequence.Undo)
        self._undo_action.triggered.connect(self._undo)
        self._undo_action.setEnabled(False)
        edit_menu.addAction(self._undo_action)
        self._redo_action = QAction("&Redo", self)
        self._redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        self._redo_action.triggered.connect(self._redo)
        self._redo_action.setEnabled(False)
        edit_menu.addAction(self._redo_action)

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction("Zoom &In", self._zoom_in, QKeySequence.ZoomIn)
        view_menu.addAction("Zoom &Out", self._zoom_out, QKeySequence.ZoomOut)
        view_menu.addAction("Fit &Width", self._zoom_fit_width, QKeySequence("Ctrl+0"))
        view_menu.addSeparator()
        self._sidebar_action = QAction("&Sidebar", self)
        self._sidebar_action.setCheckable(True)
        self._sidebar_action.setChecked(True)
        self._sidebar_action.triggered.connect(self._toggle_sidebar)
        view_menu.addAction(self._sidebar_action)
        self._toolbar_action = QAction("&Toolbar", self)
        self._toolbar_action.setCheckable(True)
        self._toolbar_action.setChecked(True)
        self._toolbar_action.triggered.connect(self._toggle_toolbar)
        view_menu.addAction(self._toolbar_action)

        # View menu extras
        view_menu.addSeparator()
        self._form_fields_action = QAction("Show &Form Fields", self)
        self._form_fields_action.setCheckable(True)
        self._form_fields_action.setChecked(False)
        self._form_fields_action.triggered.connect(self._toggle_form_fields)
        view_menu.addAction(self._form_fields_action)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")
        settings_menu.addAction("&Preferences...", self._show_settings)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&About DocView", self._show_about)

    def _setup_toolbar(self):
        self._toolbar = DocToolbar(self)
        self._toolbar.tool_selected.connect(self._on_tool_selected)
        self.addToolBar(self._toolbar)

    def _setup_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab bar
        self._tab_bar = DocTabBar()
        self._tab_bar.tab_switch_requested.connect(self._on_tab_switch)
        self._tab_bar.tab_close_requested.connect(self.close_tab)
        self._tab_bar.hide()
        main_layout.addWidget(self._tab_bar)

        # Search panel
        self._search_panel = SearchPanel()
        self._search_panel.close_requested.connect(self._on_search_close)
        main_layout.addWidget(self._search_panel)

        # Horizontal splitter: sidebar | viewport/editor | properties
        self._splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self._splitter)

        # Sidebar
        self._sidebar = SidebarPanel()
        self._sidebar.page_clicked.connect(self._on_sidebar_page_click)
        self._splitter.addWidget(self._sidebar)

        # Center stack
        self._stack = QStackedWidget()
        self._splitter.addWidget(self._stack)

        # Welcome screen (index 0)
        self._welcome = WelcomeScreen()
        self._welcome.open_file_requested.connect(self.open_file_dialog)
        self._welcome.open_recent_requested.connect(self.open_file)
        self._stack.addWidget(self._welcome)

        # PDF viewport (index 1)
        self._pdf_viewport = PDFViewport()
        self._pdf_viewport.set_tool_owner(self)
        self._pdf_viewport.page_changed.connect(self._on_page_changed)
        self._pdf_viewport.zoom_changed.connect(self._on_zoom_changed)
        self._stack.addWidget(self._pdf_viewport)

        # Markdown editor (index 2)
        self._md_editor = EditorWidget()
        self._md_editor.wikilink_clicked.connect(self._on_wikilink_clicked)
        self._md_editor.content_modified.connect(self._refresh_tabs)
        self._stack.addWidget(self._md_editor)

        # Properties panel
        self._properties_panel = PropertiesPanel()
        self._properties_panel.hide()
        self._splitter.addWidget(self._properties_panel)

        # Splitter proportions
        self._splitter.setStretchFactor(0, 0)  # sidebar fixed
        self._splitter.setStretchFactor(1, 1)  # center stretches
        self._splitter.setStretchFactor(2, 0)  # properties fixed

        # Context menu
        self._context_menu = ViewportContextMenu(self)
        self._context_menu.tool_requested.connect(self._on_tool_selected)
        self._context_menu.action_requested.connect(self.handle_toolbar_action)
        self._pdf_viewport.setContextMenuPolicy(Qt.CustomContextMenu)
        self._pdf_viewport.customContextMenuRequested.connect(
            lambda pos: self._context_menu.exec_(self._pdf_viewport.mapToGlobal(pos))
        )

    def _setup_status_bar(self):
        self._status_bar = DocStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.zoom_requested.connect(self._on_zoom_requested)
        self._status_bar.page_requested.connect(self._on_page_requested)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+F"), self, self._toggle_search)
        QShortcut(QKeySequence("Escape"), self, self._on_escape)
        QShortcut(QKeySequence("PgUp"), self, lambda: self._pdf_viewport.prev_page())
        QShortcut(QKeySequence("PgDown"), self, lambda: self._pdf_viewport.next_page())
        QShortcut(QKeySequence("Home"), self, lambda: self._pdf_viewport.go_to_page(0))
        QShortcut(QKeySequence("End"), self, self._go_to_last_page)
        QShortcut(QKeySequence("Delete"), self, self._delete_selected_annotation)

    # ── File operations ──

    def open_file_dialog(self):
        ext_filter = "All Supported (*.pdf *.md *.markdown);;PDF Files (*.pdf);;Markdown Files (*.md *.markdown);;All Files (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", ext_filter)
        if path:
            self.open_file(path)

    def open_file(self, file_path: str):
        try:
            self._save_current_state()
            self.doc_manager.open_document(file_path)
            self.recent_files.add(file_path)
            self._show_document()
            self._update_title()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    def save_file(self):
        doc = self.doc_manager.active_document
        if not doc or not doc.is_open:
            return
        if doc.file_path:
            try:
                doc.save()
                self._refresh_tabs()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        doc = self.doc_manager.active_document
        if not doc or not doc.is_open:
            return
        if doc.content_type == "pdf":
            filter_str = "PDF Files (*.pdf)"
        else:
            filter_str = "Markdown Files (*.md);;All Files (*.*)"
        path, _ = QFileDialog.getSaveFileName(self, "Save As", "", filter_str)
        if path:
            try:
                doc.save(path)
                tab = self.doc_manager.active_tab
                if tab:
                    tab.file_path = path
                self._update_title()
                self._refresh_tabs()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    # ── Tab operations ──

    def _on_tab_switch(self, index: int):
        self._save_current_state()
        self.doc_manager.switch_tab(index)
        self._restore_tab_state()
        self._show_document()
        self._update_title()

    def close_tab(self, index: int):
        tab = self.doc_manager.get_tab(index)
        if not tab:
            return
        if tab.document.modified:
            result = QMessageBox.question(
                self, "Unsaved Changes",
                f"Save changes to {tab.document.file_name}?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if result == QMessageBox.Cancel:
                return
            if result == QMessageBox.Yes:
                if index == self.doc_manager.active_index:
                    self.save_file()
                else:
                    tab.document.save()

        still_open = self.doc_manager.close_tab(index)
        if still_open:
            self._restore_tab_state()
            self._show_document()
            self._update_title()
        else:
            self._show_welcome()

    # ── Tool management ──

    def _on_tool_selected(self, tool_name: str):
        from app.tools.select_tool import SelectTool
        from app.tools.hand_tool import HandTool
        from app.tools.text_tool import TextTool
        from app.tools.highlight_tool import HighlightTool
        from app.tools.rect_tool import RectTool
        from app.tools.circle_tool import CircleTool
        from app.tools.line_tool import LineTool
        from app.tools.freehand_tool import FreehandTool
        from app.tools.redact_tool import RedactTool
        from app.tools.image_tool import ImageTool
        from app.tools.signature_tool import SignatureTool

        tool_map = {
            "select": SelectTool,
            "hand": HandTool,
            "text": TextTool,
            "highlight": HighlightTool,
            "rect": RectTool,
            "circle": CircleTool,
            "line": LineTool,
            "freehand": FreehandTool,
            "redact": RedactTool,
            "image": ImageTool,
            "signature": SignatureTool,
        }

        if tool_name in self._tool_instances:
            self.active_tool = self._tool_instances[tool_name]
        elif tool_name in tool_map:
            tool = tool_map[tool_name](self)
            self._tool_instances[tool_name] = tool
            self.active_tool = tool

        self._toolbar.set_active_tool(tool_name)

        # Show/hide properties panel
        if tool_name in ("select", "hand"):
            self._properties_panel.hide()
        else:
            self._properties_panel.show()

        # Set drag mode based on tool
        if tool_name == "hand":
            from PyQt5.QtWidgets import QGraphicsView
            self._pdf_viewport.setDragMode(QGraphicsView.ScrollHandDrag)
        else:
            from PyQt5.QtWidgets import QGraphicsView
            self._pdf_viewport.setDragMode(QGraphicsView.NoDrag)

    # ── Toolbar actions ──

    def handle_toolbar_action(self, action_name: str):
        doc = self.doc_manager.active_document
        if not doc or not doc.is_open or doc.content_type != "pdf":
            return

        if action_name == "zoom_in":
            self._zoom_in()
        elif action_name == "zoom_out":
            self._zoom_out()
        elif action_name == "fit_width":
            self._zoom_fit_width()
        elif action_name == "rotate_cw":
            from app.core.page_operations import rotate_page
            rotate_page(doc.doc, self._pdf_viewport.current_page)
            doc.modified = True
            self._pdf_viewport.load_document(doc)
            self._sidebar.load_thumbnails(doc)
        elif action_name == "rotate_ccw":
            from app.core.page_operations import rotate_page
            rotate_page(doc.doc, self._pdf_viewport.current_page, -90)
            doc.modified = True
            self._pdf_viewport.load_document(doc)
            self._sidebar.load_thumbnails(doc)
        elif action_name == "delete_page":
            if doc.page_count <= 1:
                return
            from app.core.page_operations import delete_pages
            delete_pages(doc.doc, [self._pdf_viewport.current_page])
            doc.modified = True
            self._pdf_viewport.load_document(doc)
            self._sidebar.load_thumbnails(doc)
        elif action_name == "insert_blank":
            from app.core.page_operations import insert_blank_page
            insert_blank_page(doc.doc, self._pdf_viewport.current_page + 1)
            doc.modified = True
            self._pdf_viewport.load_document(doc)
            self._sidebar.load_thumbnails(doc)
        elif action_name == "extract_text":
            text = ""
            for i in range(doc.page_count):
                text += f"--- Page {i+1} ---\n{doc.get_page(i).get_text()}\n\n"
            from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QDialogButtonBox
            dlg = QDialog(self)
            dlg.setWindowTitle("Extracted Text")
            dlg.resize(600, 400)
            lay = QVBoxLayout(dlg)
            te = QTextEdit()
            te.setPlainText(text)
            te.setReadOnly(True)
            lay.addWidget(te)
            bb = QDialogButtonBox(QDialogButtonBox.Close)
            bb.rejected.connect(dlg.close)
            lay.addWidget(bb)
            dlg.exec_()

    # ── View state ──

    def _show_welcome(self):
        self._tab_bar.hide()
        self._sidebar.hide()
        self._properties_panel.hide()
        self._welcome.refresh_recent(self.recent_files.get_all())
        self._stack.setCurrentWidget(self._welcome)
        self.setWindowTitle(WINDOW_TITLE)
        self._status_bar.update_info("", 0, 0, 1.0)

    def _show_document(self):
        doc = self.doc_manager.active_document
        if not doc:
            self._show_welcome()
            return

        self._refresh_tabs()
        self._tab_bar.show()
        self._tab_bar.set_active_tab(self.doc_manager.active_index)

        if doc.content_type == "pdf":
            self._pdf_viewport.load_document(doc)
            self._stack.setCurrentWidget(self._pdf_viewport)
            self._sidebar.show()
            self._sidebar.load_thumbnails(doc)
            self._sidebar.load_toc(doc)
            self._update_pdf_status()
            # Set search callbacks
            self._search_panel.set_callbacks(self._search_pdf, self._pdf_viewport.go_to_page)
        elif doc.content_type == "markdown":
            self._md_editor.load_document(doc)
            self._stack.setCurrentWidget(self._md_editor)
            self._sidebar.hide()
            self._properties_panel.hide()
            self._toolbar.hide()
            self._status_bar.update_info(doc.file_name, 0, 0, 1.0)

    def _refresh_tabs(self):
        self._tab_bar.refresh_tabs(self.doc_manager.get_all_tabs())

    def _update_title(self):
        doc = self.doc_manager.active_document
        if doc:
            self.setWindowTitle(f"{WINDOW_TITLE} - {doc.file_name}")
        else:
            self.setWindowTitle(WINDOW_TITLE)

    def _save_current_state(self):
        doc = self.doc_manager.active_document
        if not doc:
            return
        if doc.content_type == "pdf":
            tool_name = None
            for name, inst in self._tool_instances.items():
                if inst is self.active_tool:
                    tool_name = name
                    break
            self.doc_manager.save_viewport_state(
                self._pdf_viewport.get_scroll_y(),
                self._pdf_viewport.zoom,
                tool_name
            )

    def _restore_tab_state(self):
        tab = self.doc_manager.active_tab
        if not tab:
            return
        if tab.document.content_type == "pdf":
            self._pdf_viewport.zoom = tab.zoom
            self._pdf_viewport.load_document(tab.document)
            self._pdf_viewport.set_scroll_y(tab.scroll_y)

    def _update_pdf_status(self):
        doc = self.doc_manager.active_document
        if doc and doc.content_type == "pdf":
            self._status_bar.update_info(
                doc.file_name,
                self._pdf_viewport.current_page,
                doc.page_count,
                self._pdf_viewport.zoom
            )

    # ── Search ──

    def _search_pdf(self, query: str) -> list:
        doc = self.doc_manager.active_document
        if not doc or not doc.is_open or doc.content_type != "pdf":
            return []
        results = []
        for pn in range(doc.page_count):
            page = doc.get_page(pn)
            rects = page.search_for(query)
            if rects:
                results.append((pn, rects))
        return results

    # ── Signal handlers ──

    def _on_page_changed(self, page_num: int):
        self._update_pdf_status()
        self._sidebar.highlight_page(page_num)

    def _on_zoom_changed(self, zoom: float):
        self._update_pdf_status()

    def _on_zoom_requested(self, zoom: float):
        doc = self.doc_manager.active_document
        if doc and doc.content_type == "pdf":
            self._pdf_viewport.zoom = zoom

    def _on_page_requested(self, page: int):
        self._pdf_viewport.go_to_page(page)

    def _on_sidebar_page_click(self, page_num: int):
        # Check if it's a vault file open request
        vault_file = self._sidebar.pending_vault_file
        if vault_file:
            self.open_file(vault_file)
            return
        if page_num >= 0:
            self._pdf_viewport.go_to_page(page_num)

    def _zoom_in(self):
        self._pdf_viewport.zoom_in()

    def _zoom_out(self):
        self._pdf_viewport.zoom_out()

    def _zoom_fit_width(self):
        self._pdf_viewport.zoom_fit_width()

    def _toggle_search(self):
        if self._search_panel.is_open:
            self._search_panel._close()
        else:
            self._search_panel.open()

    def _on_search_close(self):
        pass

    # ── Undo/Redo ──

    @property
    def command_stack(self):
        tab = self.doc_manager.active_tab
        return tab.command_stack if tab else None

    def _undo(self):
        stack = self.command_stack
        if stack and stack.can_undo:
            stack.undo()
            self._refresh_page_after_command()
            self._update_undo_redo_state()

    def _redo(self):
        stack = self.command_stack
        if stack and stack.can_redo:
            stack.redo()
            self._refresh_page_after_command()
            self._update_undo_redo_state()

    def _update_undo_redo_state(self):
        stack = self.command_stack
        if stack:
            self._undo_action.setEnabled(stack.can_undo)
            self._redo_action.setEnabled(stack.can_redo)
            desc = stack.undo_description
            self._undo_action.setText(f"&Undo {desc}" if desc else "&Undo")
            desc = stack.redo_description
            self._redo_action.setText(f"&Redo {desc}" if desc else "&Redo")
        else:
            self._undo_action.setEnabled(False)
            self._redo_action.setEnabled(False)
            self._undo_action.setText("&Undo")
            self._redo_action.setText("&Redo")

    def _refresh_page_after_command(self):
        """Re-render current page after undo/redo."""
        doc = self.doc_manager.active_document
        if doc and doc.content_type == "pdf":
            items = self._pdf_viewport._page_items
            current = self._pdf_viewport.current_page
            if 0 <= current < len(items):
                items[current].invalidate()
                items[current].render(doc.doc, self._pdf_viewport.zoom)
        self._refresh_tabs()
        self._update_pdf_status()

    def _on_escape(self):
        if self._search_panel.is_open:
            self._search_panel._close()
            return
        self.active_tool = None
        self._toolbar.set_active_tool(None)
        self._properties_panel.hide()
        from PyQt5.QtWidgets import QGraphicsView
        self._pdf_viewport.setDragMode(QGraphicsView.ScrollHandDrag)

    def _go_to_last_page(self):
        doc = self.doc_manager.active_document
        if doc and doc.content_type == "pdf":
            self._pdf_viewport.go_to_page(doc.page_count - 1)

    def _delete_selected_annotation(self):
        if self.active_tool and hasattr(self.active_tool, 'delete_selected'):
            self.active_tool.delete_selected()

    def _on_wikilink_clicked(self, target: str):
        """Open a wikilink target as a new tab."""
        from app.core.obsidian.wikilinks import resolve_wikilink
        # Try to resolve against configured vault path
        from app.config import DEFAULT_VAULT_PATH
        vault_path = DEFAULT_VAULT_PATH
        current = self.doc_manager.active_document
        current_file = current.file_path if current else None

        # First try resolving from current file's directory
        if current_file:
            parent_dir = str(Path(current_file).parent)
            resolved = resolve_wikilink(target, parent_dir, current_file)
            if resolved:
                self.open_file(resolved)
                return

        # Then try vault path
        if vault_path:
            resolved = resolve_wikilink(target, vault_path, current_file)
            if resolved:
                self.open_file(resolved)
                return

        QMessageBox.information(self, "Not Found", f"Could not resolve wikilink: [[{target}]]")

    def _setup_sticky_notes(self):
        from app.ui.sticky.sticky_manager import StickyManager
        self._sticky_manager = StickyManager(self)

    def _load_vault_config(self):
        """Load vault path from config and set up sidebar."""
        from app.ui.dialogs.settings_dialog import load_config
        config = load_config()
        vault_path = config.get('vault_path', '')
        if vault_path:
            self._sidebar.set_vault_path(vault_path)

    def _show_settings(self):
        from app.ui.dialogs.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self)
        if dlg.exec_():
            vault_path = dlg.vault_path
            if vault_path:
                self._sidebar.set_vault_path(vault_path)

    def _toggle_form_fields(self, checked):
        """Show/hide interactive form field overlays."""
        self._form_fields_visible = checked
        doc = self.doc_manager.active_document
        if not doc or doc.content_type != "pdf":
            return

        if checked:
            from app.core.form_fields import FormFieldManager
            from app.ui.viewport.form_field_item import FormFieldOverlay
            from app.core.command import FormFieldEditCommand
            from app.config import RENDER_DPI

            if not self._form_field_manager:
                self._form_field_manager = FormFieldManager()

            count = self._form_field_manager.scan_document(doc)
            if count == 0:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "Form Fields", "No form fields found in this document.")
                self._form_fields_action.setChecked(False)
                return

            # Create overlays
            if self._form_field_overlay:
                self._form_field_overlay.clear()
            self._form_field_overlay = FormFieldOverlay(
                self._pdf_viewport.scene(), self._pdf_viewport.zoom)

            scale = self._pdf_viewport.zoom * RENDER_DPI / 72
            for item in self._pdf_viewport._page_items:
                fields = self._form_field_manager.get_fields(item.page_num)
                if fields:
                    rect = item.sceneBoundingRect()
                    self._form_field_overlay.show_fields(
                        fields, rect.left(), rect.top(), scale)

            # Connect value change signal
            self._form_field_overlay.signals.value_changed.connect(self._on_form_field_changed)
        else:
            if self._form_field_overlay:
                self._form_field_overlay.clear()

    def _on_form_field_changed(self, page_num: int, xref: int, old_value: str, new_value: str):
        """Handle form field value change with undo/redo."""
        from app.core.command import FormFieldEditCommand
        doc = self.doc_manager.active_document
        stack = self.command_stack
        if stack and doc:
            cmd = FormFieldEditCommand(doc, page_num, xref, old_value, new_value)
            stack.push(cmd)
            self._update_undo_redo_state()
            self._refresh_page_after_command()

    def _toggle_sidebar(self, checked):
        self._sidebar.setVisible(checked)

    def _toggle_toolbar(self, checked):
        self._toolbar.setVisible(checked)

    def _show_about(self):
        from app.version import __version__
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h2>{APP_NAME} v{__version__}</h2>"
            f"<p>PDF Viewer &bull; Markdown Editor &bull; Obsidian Integration</p>"
            f"<p>Built with PyQt5 + PyMuPDF</p>"
        )

    # ── Sticky notes (Phase 5 hooks) ──

    def create_sticky_note(self):
        if self._sticky_manager:
            self._sticky_manager.create_note()

    def show_all_sticky_notes(self):
        if self._sticky_manager:
            self._sticky_manager.show_all()

    def hide_all_sticky_notes(self):
        if self._sticky_manager:
            self._sticky_manager.hide_all()

    # ── Window events ──

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path:
                    from pathlib import Path as P
                    suffix = P(path).suffix.lower()
                    from app.config import ALL_SUPPORTED_EXTENSIONS
                    if suffix in ALL_SUPPORTED_EXTENSIONS:
                        self.open_file(path)
            event.acceptProposedAction()

    def closeEvent(self, event):
        if self.doc_manager.has_unsaved_changes():
            result = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Quit anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if result == QMessageBox.No:
                event.ignore()
                return
        event.accept()
