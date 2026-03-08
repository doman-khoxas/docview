"""Root CTk application window with multi-document support."""
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.config import WINDOW_TITLE, WINDOW_SIZE, COLOR_THEME
from app.document_manager import DocumentManager
from app.recent_files import RecentFiles
from app.preferences import Preferences
from app.core.pdf_document import PDFDocument
from app.ui.main_window import MainWindow
from app.logger import get_logger, log_exception

logger = get_logger(__name__)


class DocViewApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.prefs = Preferences()
        ctk.set_appearance_mode(self.prefs.theme)
        ctk.set_default_color_theme(COLOR_THEME)

        self.title(WINDOW_TITLE)
        self.geometry(self.prefs.window_geometry)
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
        self._setup_drag_and_drop()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        logger.info("DocViewApp initialized (theme=%s)", self.prefs.theme)

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
    # window lifecycle
    # ------------------------------------------------------------------

    def _on_close(self):
        """Save preferences and close the application."""
        self.prefs.save_window_geometry(self.geometry())
        vp = self.main_window.viewport
        self.prefs.zoom = vp.zoom
        self.prefs.save()
        self.destroy()

    def set_theme(self, theme: str):
        """Switch appearance mode: 'dark', 'light', or 'system'."""
        ctk.set_appearance_mode(theme)
        self.prefs.theme = theme
        self.prefs.save()
        logger.info("Theme changed to: %s", theme)

    # ------------------------------------------------------------------
    # drag-and-drop
    # ------------------------------------------------------------------

    def _setup_drag_and_drop(self):
        """Enable drag-and-drop file opening (Windows)."""
        try:
            import windnd
            windnd.hook_dropfiles(self, func=self._on_files_dropped)
            logger.info("Drag-and-drop enabled via windnd")
        except ImportError:
            logger.debug("windnd not available — drag-and-drop disabled")

    def _on_files_dropped(self, file_list):
        """Handle files dropped onto the window."""
        _SUPPORTED = (
            {".pdf", ".html", ".htm", ".md", ".markdown", ".mdown", ".mkd"}
            | self._IMAGE_EXTENSIONS
        )
        for raw in file_list:
            path = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            ext = os.path.splitext(path)[1].lower()
            if ext in _SUPPORTED:
                logger.info("File dropped: %s", path)
                self.open_file(path)
                return  # open first valid file
        logger.debug("Dropped files had no supported extension")

    # ------------------------------------------------------------------
    # file operations
    # ------------------------------------------------------------------

    # Supported file extensions by type
    _HTML_EXTENSIONS = {".html", ".htm"}
    _MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd"}
    _IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp", ".gif"}

    def open_file_dialog(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("All supported",
                 "*.pdf *.html *.htm *.md *.markdown "
                 "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.gif"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.gif"),
                ("HTML files", "*.html *.htm"),
                ("Markdown files", "*.md *.markdown"),
                ("All files", "*.*"),
            ]
        )
        if path:
            self.open_file(path)

    def open_file(self, file_path: str):
        import os
        logger.info("Opening file: %s", file_path)

        ext = os.path.splitext(file_path)[1].lower()

        # Route HTML/Markdown files to the HTML viewport
        if ext in self._HTML_EXTENSIONS or ext in self._MARKDOWN_EXTENSIONS:
            try:
                from pathlib import Path
                self.recent_files.add(file_path)
                self.main_window.show_html(file_path)
                name = Path(file_path).name
                self.title(f"{WINDOW_TITLE} - {name}")
                logger.info("HTML/MD file opened: %s", name)
            except Exception as e:
                log_exception(logger, "Failed to open HTML/MD file", e)
                messagebox.showerror("Error", f"Failed to open file:\n{e}")
            return

        # Image file handling — convert to searchable PDF via OCR
        if ext in self._IMAGE_EXTENSIONS:
            self._open_image_as_pdf(file_path)
            return

        # PDF file handling
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
                logger.info("File opened successfully: %s (%d pages)",
                            doc.file_name, doc.page_count)
        except Exception as e:
            log_exception(logger, "Failed to open PDF", e)
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
                    logger.debug("Save cancelled by user for %s", doc.file_name)
                    return
            try:
                doc.save()
                logger.info("File saved: %s", doc.file_path)
                self.update_status()
                self.main_window.tab_bar.refresh()
            except Exception as e:
                log_exception(logger, "Failed to save file", e)
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
                logger.info("File saved as: %s", path)
                self.title(f"{WINDOW_TITLE} - {doc.file_name}")
                self.update_status()
                self.main_window.tab_bar.refresh()
            except Exception as e:
                log_exception(logger, "Failed to save file as", e)
                messagebox.showerror("Error", f"Failed to save:\n{e}")

    # ------------------------------------------------------------------
    # image → PDF conversion
    # ------------------------------------------------------------------

    def _open_image_as_pdf(self, image_path: str):
        """Convert an image to a searchable PDF and open it."""
        import threading
        from pathlib import Path

        name = Path(image_path).stem
        logger.info("Opening image as PDF: %s", image_path)

        # Check if ocrmypdf is available
        try:
            import ocrmypdf  # noqa: F401
        except ImportError:
            messagebox.showerror(
                "OCR Required",
                "Opening image files requires OCRmyPDF.\n\n"
                "Install with:\n  pip install ocrmypdf\n\n"
                "Tesseract OCR must also be installed on your system.")
            return

        # Ask where to save the PDF
        pdf_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"{name}.pdf",
            title="Save converted PDF as"
        )
        if not pdf_path:
            return

        # Show a progress dialog
        progress = ctk.CTkToplevel(self)
        progress.title("Converting Image")
        progress.geometry("360x120")
        progress.resizable(False, False)
        progress.transient(self)
        progress.grab_set()

        ctk.CTkLabel(
            progress, text=f"Converting {Path(image_path).name} to PDF...",
            font=ctk.CTkFont(family="Segoe UI", size=12)
        ).pack(padx=20, pady=(20, 8))

        bar = ctk.CTkProgressBar(progress, width=300)
        bar.pack(padx=20, pady=8)
        bar.configure(mode="indeterminate")
        bar.start()

        # Center
        progress.update_idletasks()
        pw, ph = self.winfo_width(), self.winfo_height()
        px, py = self.winfo_x(), self.winfo_y()
        w, h = progress.winfo_width(), progress.winfo_height()
        progress.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

        def convert():
            try:
                from app.core.image_to_pdf import image_to_pdf
                image_to_pdf(image_path, pdf_path)
                self.after(0, lambda: _on_done(None))
            except Exception as e:
                log_exception(logger, "Image→PDF conversion failed", e)
                self.after(0, lambda err=str(e): _on_done(err))

        def _on_done(error):
            bar.stop()
            progress.grab_release()
            progress.destroy()
            if error:
                messagebox.showerror(
                    "Conversion Error",
                    f"Failed to convert image to PDF:\n\n{error}")
            else:
                self.open_file(pdf_path)

        threading.Thread(target=convert, daemon=True).start()

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
        from app.tools.underline_tool import UnderlineTool
        from app.tools.strikeout_tool import StrikeoutTool
        from app.tools.rect_tool import RectTool
        from app.tools.circle_tool import CircleTool
        from app.tools.line_tool import LineTool
        from app.tools.arrow_tool import ArrowTool
        from app.tools.freehand_tool import FreehandTool
        from app.tools.redact_tool import RedactTool
        from app.tools.image_tool import ImageTool
        from app.tools.sticky_note_tool import StickyNoteTool
        from app.tools.stamp_tool import StampTool

        tool_map = {
            "select": SelectTool,
            "text": TextTool,
            "highlight": HighlightTool,
            "underline": UnderlineTool,
            "strikeout": StrikeoutTool,
            "rect": RectTool,
            "circle": CircleTool,
            "line": LineTool,
            "arrow": ArrowTool,
            "freehand": FreehandTool,
            "redact": RedactTool,
            "image": ImageTool,
            "sticky_note": StickyNoteTool,
            "stamp": StampTool,
        }

        if tool_name in self._tool_instances:
            self.active_tool = self._tool_instances[tool_name]
        elif tool_name in tool_map:
            tool = tool_map[tool_name](self)
            self._tool_instances[tool_name] = tool
            self.active_tool = tool

        self.main_window.toolbar.highlight_tool(tool_name)
        logger.debug("Tool activated: %s", tool_name)

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
        logger.debug("Undo push: page=%d, type=%s (stack=%d)",
                      page_num, type(annotation).__name__, len(self._undo_stack))

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
            logger.info("Applied %d redaction(s) permanently", count)
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
        logger.info("Print requested")

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
            log_exception(logger, "Print failed", e)
            messagebox.showerror("Print Error", f"Failed to print:\n{e}")
