"""Root CTk application window with multi-document support."""
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.config import WINDOW_TITLE, WINDOW_SIZE, APPEARANCE_MODE, COLOR_THEME
from app.document_manager import DocumentManager
from app.recent_files import RecentFiles
from app.core.pdf_document import PDFDocument
from app.ui.main_window import MainWindow


class DocViewApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)

        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(800, 600)

        # --- App icon ---
        self._set_icon()

        self.doc_manager = DocumentManager()
        self.recent_files = RecentFiles()
        self.active_tool = None
        self._tool_instances: dict[str, object] = {}
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []

        self.main_window = MainWindow(self, self)

        self._bind_shortcuts()

    def _set_icon(self):
        """Set the window icon from assets/."""
        try:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ico_path = os.path.join(base, "assets", "docview.ico")
            png_path = os.path.join(base, "assets", "docview.png")
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
            elif os.path.exists(png_path):
                from tkinter import PhotoImage
                icon = PhotoImage(file=png_path)
                self.iconphoto(True, icon)
        except Exception:
            pass  # non-critical — fall back to default icon

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
        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-y>", lambda e: self.redo())
        self.bind("<Control-Shift-Z>", lambda e: self.redo())
        self.bind("<Escape>", lambda e: self._on_escape())
        self.bind("<Control-plus>", lambda e: self.main_window.viewport.zoom_in())
        self.bind("<Control-equal>", lambda e: self.main_window.viewport.zoom_in())
        self.bind("<Control-minus>", lambda e: self.main_window.viewport.zoom_out())
        self.bind("<Prior>", lambda e: self.main_window.viewport.prev_page())
        self.bind("<Next>", lambda e: self.main_window.viewport.next_page())
        self.bind("<Left>", lambda e: self.main_window.viewport.prev_page())
        self.bind("<Right>", lambda e: self.main_window.viewport.next_page())
        self.bind("<Up>", lambda e: self._scroll_viewport(-60))
        self.bind("<Down>", lambda e: self._scroll_viewport(60))
        self.bind("<Home>", lambda e: self.main_window.viewport.go_to_page(0))
        self.bind("<End>", lambda e: self._go_to_last_page())
        self.bind("<Delete>", lambda e: self._delete_selected_annotation())
        self.bind("<Control-p>", lambda e: self.print_document())
        self.bind("<Control-b>", lambda e: self.main_window.sidebar.toggle())

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
            doc = self.pdf_doc
            if doc:
                self.title(f"{WINDOW_TITLE} - {doc.file_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF:\n{e}")

    def save_file(self):
        doc = self.pdf_doc
        if not doc or not doc.is_open:
            return
        if doc.file_path:
            # Confirm overwrite of existing file
            if os.path.exists(doc.file_path):
                confirm = messagebox.askyesno(
                    "Confirm Save",
                    f"Overwrite '{doc.file_name}'?")
                if not confirm:
                    return
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
        doc = self.pdf_doc
        self.title(f"{WINDOW_TITLE} - {doc.file_name}" if doc else WINDOW_TITLE)

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
        from app.tools.redact_tool import RedactTool
        from app.tools.image_tool import ImageTool

        tool_map = {
            "select": SelectTool,
            "text": TextTool,
            "highlight": HighlightTool,
            "rect": RectTool,
            "circle": CircleTool,
            "line": LineTool,
            "freehand": FreehandTool,
            "redact": RedactTool,
            "image": ImageTool,
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
            self.main_window.toolbar.update_zoom_label(vp.zoom)
        else:
            self.main_window.status_bar.update_info("", 0, 0, 1.0)
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

    def toggle_overview(self):
        """Toggle the all-pages document overview grid."""
        self.main_window.overview_panel.show()

    def _toggle_search(self):
        sp = self.main_window.search_panel
        if sp.is_open:
            sp.close()
        else:
            sp.open()

    def _on_escape(self):
        # close overview if open
        op = self.main_window.overview_panel
        if op.is_open:
            op.hide()
            return
        sp = self.main_window.search_panel
        if sp.is_open:
            sp.close()
            return
        # deselect tool -> hand mode
        self.active_tool = None
        self.main_window.toolbar.highlight_tool(None)
        self.main_window.properties_panel.hide()

    def _scroll_viewport(self, delta: int):
        """Scroll the viewport by delta pixels."""
        vp = self.main_window.viewport
        vp.canvas.yview_scroll(delta, "units")

    def _go_to_last_page(self):
        doc = self.pdf_doc
        if doc and doc.is_open:
            self.main_window.viewport.go_to_page(doc.page_count - 1)

    def _delete_selected_annotation(self):
        if self.active_tool and hasattr(self.active_tool, 'delete_selected'):
            getattr(self.active_tool, 'delete_selected')()

    # ------------------------------------------------------------------
    # undo / redo (annotation level)
    # ------------------------------------------------------------------

    def push_undo(self, page_num: int, annotation):
        """Push an annotation onto the undo stack (called by tools after add)."""
        self._undo_stack.append({"page": page_num, "annotation": annotation})
        self._redo_stack.clear()  # new action invalidates redo history

    def undo(self):
        """Undo the last annotation (Ctrl+Z)."""
        if not self._undo_stack:
            return
        entry = self._undo_stack.pop()
        doc = self.pdf_doc
        if doc and doc.is_open:
            doc.remove_pending_annotation(entry["page"], entry["annotation"])
            self._redo_stack.append(entry)
            self.main_window.viewport.render_current_page()
            self.update_status()

    def redo(self):
        """Redo the last undone annotation (Ctrl+Y / Ctrl+Shift+Z)."""
        if not self._redo_stack:
            return
        entry = self._redo_stack.pop()
        doc = self.pdf_doc
        if doc and doc.is_open:
            doc.add_pending_annotation(entry["page"], entry["annotation"])
            self._undo_stack.append(entry)
            self.main_window.viewport.render_current_page()
            self.update_status()

    # ------------------------------------------------------------------
    # redaction
    # ------------------------------------------------------------------

    def apply_redactions(self):
        """Apply all pending RedactAnnotation entries permanently."""
        import fitz
        from app.core.annotation_model import RedactAnnotation
        doc = self.pdf_doc
        if not doc or not doc.is_open:
            return

        count = 0
        for page_num in list(doc.get_all_pending_annotations().keys()):
            page = doc.get_page(page_num)
            annots = doc.get_pending_annotations(page_num)
            redacts = [a for a in annots if isinstance(a, RedactAnnotation)]
            for r in redacts:
                rect = fitz.Rect(r.x0, r.y0, r.x1, r.y1)
                page.add_redact_annot(rect, fill=(0, 0, 0))
                count += 1
            if redacts:
                page.apply_redactions()
                # remove applied redactions from pending
                for r in redacts:
                    doc.remove_pending_annotation(page_num, r)

        if count > 0:
            doc.modified = True
            self.main_window.viewport.load_document()
            self.update_status()
            messagebox.showinfo(
                "Redaction Applied",
                f"Applied {count} redaction(s) permanently.\nRemember to save the file.")
        else:
            messagebox.showinfo("No Redactions", "No pending redactions to apply.")

    def clear_redactions(self):
        """Remove all pending RedactAnnotation entries without applying."""
        from app.core.annotation_model import RedactAnnotation
        doc = self.pdf_doc
        if not doc or not doc.is_open:
            return

        for page_num in list(doc.get_all_pending_annotations().keys()):
            annots = doc.get_pending_annotations(page_num)
            redacts = [a for a in annots if isinstance(a, RedactAnnotation)]
            for r in redacts:
                doc.remove_pending_annotation(page_num, r)

        self.main_window.viewport.render_current_page()
        self.update_status()

    # ------------------------------------------------------------------
    # printing
    # ------------------------------------------------------------------

    def print_document(self):
        """Print the current PDF using the OS print system."""
        import subprocess
        import sys
        import tempfile

        doc = self.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Print", "No document open to print.")
            return

        file_path = doc.file_path
        if not file_path:
            # Save to temp file first if unsaved
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            try:
                doc.doc.save(tmp.name)
                file_path = tmp.name
            except Exception as e:
                messagebox.showerror("Print Error", f"Could not prepare document:\n{e}")
                return

        try:
            if sys.platform == "win32":
                # Windows: use the default PDF handler's print verb
                os.startfile(file_path, "print")
            elif sys.platform == "darwin":
                subprocess.Popen(["lpr", file_path])
            else:
                # Linux
                subprocess.Popen(["lp", file_path])
        except Exception as e:
            messagebox.showerror("Print Error", f"Failed to print:\n{e}")
