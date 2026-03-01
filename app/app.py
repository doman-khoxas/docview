"""Root CTk application window with multi-document support."""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.config import WINDOW_TITLE, WINDOW_SIZE, APPEARANCE_MODE, COLOR_THEME
from app.document_manager import DocumentManager
from app.recent_files import RecentFiles
from app.core.pdf_document import PDFDocument
from app.ui.main_window import MainWindow


class PDFEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)

        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(800, 600)

        self.doc_manager = DocumentManager()
        self.recent_files = RecentFiles()
        self.active_tool = None
        self._tool_instances: dict[str, object] = {}

        self.main_window = MainWindow(self, self)

        self._bind_shortcuts()

    # ------------------------------------------------------------------
    # convenience property so tools / UI can do app.pdf_doc
    # ------------------------------------------------------------------

    @property
    def pdf_doc(self) -> PDFDocument | None:
        return self.doc_manager.active_document

    # ------------------------------------------------------------------
    # shortcuts
    # ------------------------------------------------------------------

    def _bind_shortcuts(self):
        self.bind("<Control-o>", lambda e: self.open_file_dialog())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-Shift-S>", lambda e: self.save_file_as())
        self.bind("<Control-w>", lambda e: self.close_tab(self.doc_manager.active_index))
        self.bind("<Control-f>", lambda e: self._toggle_search())
        self.bind("<Escape>", lambda e: self._on_escape())
        self.bind("<Control-plus>", lambda e: self.main_window.viewport.zoom_in())
        self.bind("<Control-equal>", lambda e: self.main_window.viewport.zoom_in())
        self.bind("<Control-minus>", lambda e: self.main_window.viewport.zoom_out())
        self.bind("<Prior>", lambda e: self.main_window.viewport.prev_page())
        self.bind("<Next>", lambda e: self.main_window.viewport.next_page())
        self.bind("<Home>", lambda e: self.main_window.viewport.go_to_page(0))
        self.bind("<End>", lambda e: self._go_to_last_page())
        self.bind("<Delete>", lambda e: self._delete_selected_annotation())

    # ------------------------------------------------------------------
    # file operations
    # ------------------------------------------------------------------

    def open_file_dialog(self):
        path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if path:
            self.open_file(path)

    def open_file(self, file_path: str):
        try:
            # save current viewport state before switching
            self._save_current_state()

            self.doc_manager.open_document(file_path)
            self.recent_files.add(file_path)
            self.main_window.show_document()
            self.update_status()
            self.title(f"{WINDOW_TITLE} - {self.pdf_doc.file_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF:\n{e}")

    def save_file(self):
        doc = self.pdf_doc
        if not doc or not doc.is_open:
            return
        if doc.file_path:
            try:
                doc.save()
                self.update_status()
                self.main_window.tab_bar.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save:\n{e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        doc = self.pdf_doc
        if not doc or not doc.is_open:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if path:
            try:
                doc.save(path)
                tab = self.doc_manager.active_tab
                if tab:
                    tab.file_path = path
                self.title(f"{WINDOW_TITLE} - {doc.file_name}")
                self.update_status()
                self.main_window.tab_bar.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save:\n{e}")

    # ------------------------------------------------------------------
    # tab operations
    # ------------------------------------------------------------------

    def switch_tab(self, index: int):
        self._save_current_state()
        self.doc_manager.switch_tab(index)
        self._restore_tab_state()
        self.main_window.show_document()
        self.update_status()
        self.title(f"{WINDOW_TITLE} - {self.pdf_doc.file_name}")

    def close_tab(self, index: int):
        tab = self.doc_manager.get_tab(index)
        if not tab:
            return
        if tab.pdf_doc.modified:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Save changes to {tab.pdf_doc.file_name}?")
            if result is None:  # Cancel
                return
            if result:  # Yes
                if index == self.doc_manager.active_index:
                    self.save_file()
                else:
                    tab.pdf_doc.save()

        still_open = self.doc_manager.close_tab(index)
        if still_open:
            self._restore_tab_state()
            self.main_window.show_document()
            self.update_status()
            doc = self.pdf_doc
            self.title(f"{WINDOW_TITLE} - {doc.file_name}" if doc else WINDOW_TITLE)
        else:
            self.main_window.show_welcome()
            self.title(WINDOW_TITLE)

    # ------------------------------------------------------------------
    # tool management
    # ------------------------------------------------------------------

    def set_tool(self, tool_name: str):
        from app.tools.select_tool import SelectTool
        from app.tools.text_tool import TextTool
        from app.tools.highlight_tool import HighlightTool
        from app.tools.rect_tool import RectTool
        from app.tools.circle_tool import CircleTool
        from app.tools.line_tool import LineTool
        from app.tools.freehand_tool import FreehandTool

        tool_map = {
            "select": SelectTool,
            "text": TextTool,
            "highlight": HighlightTool,
            "rect": RectTool,
            "circle": CircleTool,
            "line": LineTool,
            "freehand": FreehandTool,
        }

        if tool_name in self._tool_instances:
            self.active_tool = self._tool_instances[tool_name]
        elif tool_name in tool_map:
            tool = tool_map[tool_name](self)
            self._tool_instances[tool_name] = tool
            self.active_tool = tool

        self.main_window.toolbar.highlight_tool(tool_name)

        # show properties panel when annotation tool is active
        self.main_window.properties_panel.show()

    # ------------------------------------------------------------------
    # status
    # ------------------------------------------------------------------

    def update_status(self):
        doc = self.pdf_doc
        vp = self.main_window.viewport
        if doc and doc.is_open:
            self.main_window.status_bar.update_info(
                doc.file_name, vp.current_page, doc.page_count, vp.zoom)
            self.main_window.toolbar.update_page_label(vp.current_page, doc.page_count)
            self.main_window.toolbar.update_zoom_label(vp.zoom)
        else:
            self.main_window.status_bar.update_info("", 0, 0, 1.0)
            self.main_window.toolbar.update_page_label(0, 0)
            self.main_window.toolbar.update_zoom_label(1.0)

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _save_current_state(self):
        vp = self.main_window.viewport
        tool_name = None
        for name, inst in self._tool_instances.items():
            if inst is self.active_tool:
                tool_name = name
                break
        self.doc_manager.save_viewport_state(vp.get_scroll_y(), vp.zoom, tool_name)

    def _restore_tab_state(self):
        tab = self.doc_manager.active_tab
        if not tab:
            return
        vp = self.main_window.viewport
        vp.zoom = tab.zoom
        vp.load_document()
        vp.set_scroll_y(tab.scroll_y)
        if tab.active_tool_name:
            self.set_tool(tab.active_tool_name)
        else:
            self.active_tool = None
            self.main_window.toolbar.highlight_tool(None)
            self.main_window.properties_panel.hide()

    def _toggle_search(self):
        sp = self.main_window.search_panel
        if sp.is_open:
            sp.close()
        else:
            sp.open()

    def _on_escape(self):
        sp = self.main_window.search_panel
        if sp.is_open:
            sp.close()
            return
        # deselect tool -> hand mode
        self.active_tool = None
        self.main_window.toolbar.highlight_tool(None)
        self.main_window.properties_panel.hide()

    def _go_to_last_page(self):
        doc = self.pdf_doc
        if doc and doc.is_open:
            self.main_window.viewport.go_to_page(doc.page_count - 1)

    def _delete_selected_annotation(self):
        if self.active_tool and hasattr(self.active_tool, 'delete_selected'):
            self.active_tool.delete_selected()
