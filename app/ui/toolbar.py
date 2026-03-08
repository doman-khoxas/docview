"""Sleek ribbon toolbar — modern, minimal, user-friendly layout."""
import customtkinter as ctk
from app.config import (
    BG_ABYSS, BG_PANEL, BORDER_RED, TEXT_RED,
    HOVER_RED, ACTIVE_RED, TEXT_MUTED, CORNER_RADIUS, RENDER_DPI,
    ACCENT, ACCENT_HOVER, TEXT_PRIMARY, TEXT_SECONDARY, BG_SURFACE,
    BG_ACTIVE, ACCENT_MUTED, BORDER_DEFAULT, BORDER_SUBTLE,
    COLOR_DANGER, BG_HOVER
)
from app.logger import get_logger, log_exception

logger = get_logger(__name__)

_TAB_CATEGORIES = ["Home", "Edit", "Page", "Tools"]

# Refined sizing — taller buttons, cleaner spacing
_SYM_SIZE = 18
_LBL_SIZE = 9
_BTN_HEIGHT = 56


class _RibbonButton(ctk.CTkFrame):
    """Sleek ribbon button: icon above, label below, smooth hover."""

    def __init__(self, parent, symbol: str, label: str, command=None,
                 width=58, tool_name=None, accent=False, danger=False):
        super().__init__(parent, fg_color="transparent", corner_radius=6,
                         width=width, height=_BTN_HEIGHT,
                         border_width=0)
        self.pack_propagate(False)
        self._command = command
        self._tool_name = tool_name
        self._default_fg = "transparent"
        self._accent = accent
        self._danger = danger

        sym_color = ACCENT if accent else (COLOR_DANGER if danger else TEXT_PRIMARY)

        self._sym = ctk.CTkLabel(
            self, text=symbol,
            font=ctk.CTkFont(family="Segoe UI Symbol", size=_SYM_SIZE),
            text_color=sym_color, cursor="hand2"
        )
        self._sym.pack(expand=True, pady=(6, 0))

        self._lbl = ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(family="Segoe UI", size=_LBL_SIZE),
            text_color=TEXT_MUTED, cursor="hand2"
        )
        self._lbl.pack(pady=(0, 4))

        for widget in [self, self._sym, self._lbl]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_click(self, event=None):
        if self._command:
            self._command()

    def _on_enter(self, event=None):
        if self.cget("fg_color") != ACCENT_MUTED:
            self.configure(fg_color=BG_HOVER)
            self._lbl.configure(text_color=TEXT_SECONDARY)

    def _on_leave(self, event=None):
        if self.cget("fg_color") != ACCENT_MUTED:
            self.configure(fg_color=self._default_fg)
            self._lbl.configure(text_color=TEXT_MUTED)

    def set_active(self, active: bool):
        if active:
            self.configure(fg_color=ACCENT_MUTED)
            self._lbl.configure(text_color=ACCENT)
        else:
            self.configure(fg_color="transparent")
            self._default_fg = "transparent"
            self._lbl.configure(text_color=TEXT_MUTED)


class Toolbar(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(
            parent,
            fg_color=BG_SURFACE,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=0
        )
        self.app_ref = app_ref

        # --- Row 1: Tab Strip (pill-style tabs) ---
        self._tab_row = ctk.CTkFrame(self, height=34, fg_color=BG_PANEL, corner_radius=0)
        self._tab_row.pack(fill="x")
        self._tab_row.pack_propagate(False)

        # Left spacer
        ctk.CTkFrame(self._tab_row, width=8, fg_color="transparent").pack(side="left")

        self._cat_buttons: dict[str, ctk.CTkButton] = {}
        for cat in _TAB_CATEGORIES:
            btn = ctk.CTkButton(
                self._tab_row, text=cat, width=72, height=28,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                fg_color="transparent",
                text_color=TEXT_MUTED,
                hover_color=BG_HOVER,
                corner_radius=6,
                command=lambda c=cat: self._switch_category(c)
            )
            btn.pack(side="left", padx=2, pady=3)
            self._cat_buttons[cat] = btn

        # Accent underline
        self._accent_line = ctk.CTkFrame(self, height=2, fg_color=ACCENT, corner_radius=0)
        self._accent_line.pack(fill="x")

        # --- Row 2: Ribbon Panel ---
        self._ribbon = ctk.CTkFrame(self, height=80, fg_color=BG_SURFACE, corner_radius=0)
        self._ribbon.pack(fill="x")
        self._ribbon.pack_propagate(False)

        self._panels: dict[str, ctk.CTkFrame] = {}
        self._tool_buttons: dict[str | None, _RibbonButton] = {}

        self._build_home_panel()
        self._build_edit_panel()
        self._build_page_panel()
        self._build_tools_panel()

        self._active_cat = None
        self._switch_category("Home")

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    def _rb(self, parent, symbol: str, label: str,
            command=None, tool_name=None, width=58,
            accent=False, danger=False) -> _RibbonButton:
        cmd = command if command else (lambda t=tool_name: self._set_tool(t))
        btn = _RibbonButton(parent, symbol, label, command=cmd,
                            width=width, tool_name=tool_name,
                            accent=accent, danger=danger)
        if tool_name is not None:
            self._tool_buttons[tool_name] = btn
        return btn

    def _sep(self, parent):
        """Thin vertical separator."""
        sep = ctk.CTkFrame(parent, width=1, fg_color=BORDER_SUBTLE, corner_radius=0)
        sep.pack(side="left", fill="y", padx=8, pady=12)
        return sep

    def _group(self, parent, title: str) -> ctk.CTkFrame:
        """Tool group with subtle bottom label."""
        outer = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        outer.pack(side="left", padx=1, pady=1, fill="y")

        content = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
        content.pack(side="top", fill="both", expand=True, padx=2, pady=(2, 0))

        ctk.CTkLabel(
            outer, text=title.upper(),
            font=ctk.CTkFont(family="Segoe UI", size=8, weight="bold"),
            text_color=TEXT_MUTED
        ).pack(side="bottom", pady=(0, 2))

        return content

    # ------------------------------------------------------------------
    # Tab Panels — reorganized for better workflow
    # ------------------------------------------------------------------

    def _build_home_panel(self):
        """Home: File ops, view controls, navigation — the essentials."""
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Home"] = p

        # File group — most used actions first
        g = self._group(p, "File")
        self._rb(g, "\u2750", "Open", self.app_ref.open_file_dialog, accent=True).pack(side="left", padx=1)
        self._rb(g, "\u2913", "Save", self.app_ref.save_file).pack(side="left", padx=1)
        self._rb(g, "\u2912", "Save As", self.app_ref.save_file_as, width=54).pack(side="left", padx=1)

        self._sep(p)

        # Undo/Redo
        g = self._group(p, "Edit")
        self._rb(g, "\u21B6", "Undo", self.app_ref.undo, width=50).pack(side="left", padx=1)
        self._rb(g, "\u21B7", "Redo", self.app_ref.redo, width=50).pack(side="left", padx=1)

        self._sep(p)

        # Zoom — compact inline with label
        g = self._group(p, "Zoom")
        self._rb(g, "\u2212", "Out", self._zoom_out, width=42).pack(side="left", padx=1)

        self.zoom_label = ctk.CTkLabel(
            g, text="100%", width=46,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.zoom_label.pack(side="left", padx=2)

        self._rb(g, "+", "In", self._zoom_in, width=42).pack(side="left", padx=1)
        self._rb(g, "\u2922", "Fit", self._zoom_fit, width=42).pack(side="left", padx=1)

        self._sep(p)

        # Navigate
        g = self._group(p, "Navigate")
        self._rb(g, "\u25C0", "Prev", self._prev_page, width=46).pack(side="left", padx=1)
        self._rb(g, "\u25B6", "Next", self._next_page, width=46).pack(side="left", padx=1)

        self._sep(p)

        # Mode
        g = self._group(p, "Mode")
        self._rb(g, "\u2710", "Select", tool_name="select", width=54).pack(side="left", padx=1)
        self._rb(g, "\u270B", "Hand", tool_name="hand", width=50).pack(side="left", padx=1)

        self._sep(p)

        # Print + Theme + About
        g = self._group(p, "More")
        self._rb(g, "\u2399", "Print", self.app_ref.print_document, width=50).pack(side="left", padx=1)
        self._rb(g, "\u263E", "Theme", command=self._toggle_theme, width=50).pack(side="left", padx=1)
        self._rb(g, "\u24D8", "About", command=self._show_about, width=50).pack(side="left", padx=1)

    def _build_edit_panel(self):
        """Edit: All annotation/drawing tools in one view."""
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Edit"] = p

        # Draw
        g = self._group(p, "Draw")
        self._rb(g, "\u270E", "Pen", tool_name="freehand", accent=True).pack(side="left", padx=1)
        self._rb(g, "\u2591", "Highlight", tool_name="highlight", width=62).pack(side="left", padx=1)

        self._sep(p)

        # Markup
        g = self._group(p, "Markup")
        self._rb(g, "\u0332A\u0332", "Underline", tool_name="underline", width=62).pack(side="left", padx=1)
        self._rb(g, "\u0336A\u0336", "Strike", tool_name="strikeout", width=50).pack(side="left", padx=1)

        self._sep(p)

        # Shapes — all together
        g = self._group(p, "Shapes")
        self._rb(g, "\u25AD", "Rect", tool_name="rect", width=50).pack(side="left", padx=1)
        self._rb(g, "\u25EF", "Circle", tool_name="circle", width=50).pack(side="left", padx=1)
        self._rb(g, "\u2571", "Line", tool_name="line", width=50).pack(side="left", padx=1)
        self._rb(g, "\u2794", "Arrow", tool_name="arrow", width=50).pack(side="left", padx=1)

        self._sep(p)

        # Text + Image + Notes
        g = self._group(p, "Insert")
        self._rb(g, "A", "Text", tool_name="text", width=50).pack(side="left", padx=1)
        self._rb(g, "\u2316", "Image", tool_name="image", width=50).pack(side="left", padx=1)
        self._rb(g, "\u2709", "Note", tool_name="sticky_note", width=50).pack(side="left", padx=1)
        self._rb(g, "\u2318", "Stamp", tool_name="stamp", width=50).pack(side="left", padx=1)

    def _build_page_panel(self):
        """Page: Page management, rotation, optimization."""
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Page"] = p

        # Create
        g = self._group(p, "Create")
        self._rb(g, "\u2795", "New", command=self._new_document, accent=True, width=50).pack(side="left", padx=1)
        self._rb(g, "\u25A1", "Blank", command=self._insert_blank, width=50).pack(side="left", padx=1)
        self._rb(g, "\u2913", "Insert", command=self._insert_pages_from_file, width=50).pack(side="left", padx=1)

        self._sep(p)

        # Manage
        g = self._group(p, "Manage")
        self._rb(g, "\u2702", "Extract", command=self._extract_pages, width=56).pack(side="left", padx=1)
        self._rb(g, "\u21E9", "Export", command=self._export_as_image, width=52).pack(side="left", padx=1)
        self._rb(g, "\u2717", "Delete", command=self._delete_pages_mode, danger=True, width=52).pack(side="left", padx=1)

        self._sep(p)

        # Rotate
        g = self._group(p, "Rotate")
        self._rb(g, "\u21BA", "Left", command=self._rotate_left, width=46).pack(side="left", padx=1)
        self._rb(g, "\u21BB", "Right", command=self._rotate_right, width=46).pack(side="left", padx=1)

        self._sep(p)

        # Optimize
        g = self._group(p, "Optimize")
        self._rb(g, "\u2318", "Compress", command=self._compress_document, width=64).pack(side="left", padx=1)
        self._rb(g, "\u2756", "Watermark", command=self._add_watermark, width=68).pack(side="left", padx=1)

        self._sep(p)

        # Page range (inline)
        g = self._group(p, "Page Range")
        self._page_range_var = ctk.StringVar(value="")
        range_entry = ctk.CTkEntry(
            g, textvariable=self._page_range_var,
            width=110, height=26, placeholder_text="1,8,10-12",
            fg_color=BG_PANEL, border_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4
        )
        range_entry.pack(side="left", padx=4, pady=8)
        range_entry.bind("<Return>", lambda e: self._apply_page_range())
        self._rb(g, "\u2713", "Go", command=self._apply_page_range, width=42, accent=True).pack(side="left", padx=1)

    def _build_tools_panel(self):
        """Tools: Security, redaction, signatures."""
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Tools"] = p

        # Redaction
        g = self._group(p, "Redaction")
        self._rb(g, "\u2588", "Redact", tool_name="redact", danger=True).pack(side="left", padx=1)
        self._rb(g, "\u2713", "Apply", command=self._on_apply_redactions, accent=True, width=52).pack(side="left", padx=1)
        self._rb(g, "\u2717", "Clear", command=self._on_clear_redactions, width=50).pack(side="left", padx=1)

        self._sep(p)

        # Security
        g = self._group(p, "Security")
        self._rb(g, "\u26BF", "Protect", command=self._protect_document, accent=True).pack(side="left", padx=1)
        self._rb(g, "\u270D", "Sign", command=self._sign_document).pack(side="left", padx=1)
        self._rb(g, "\u2327", "Strip\nMeta", command=self._strip_metadata, width=54).pack(side="left", padx=1)

        self._sep(p)

        # Forms
        g = self._group(p, "Forms")
        self._rb(g, "\u2610", "Fill\nForms", command=self._toggle_form_fill, accent=True, width=54).pack(side="left", padx=1)
        self._rb(g, "\u2713", "Save\nFields", command=self._save_form_fields, width=54).pack(side="left", padx=1)

        self._sep(p)

        # OCR
        g = self._group(p, "OCR")
        self._rb(g, "\u2399", "OCR", command=self._run_ocr).pack(side="left", padx=1)

        self._sep(p)

        # Text Editing
        g = self._group(p, "Edit Text")
        self._rb(g, "\u2710", "Find &\nReplace", command=self._find_replace, width=60).pack(side="left", padx=1)

    # ------------------------------------------------------------------
    # Tab switching
    # ------------------------------------------------------------------

    def _switch_category(self, cat: str):
        if self._active_cat == cat:
            return
        self._active_cat = cat

        for c, btn in self._cat_buttons.items():
            if c == cat:
                btn.configure(fg_color=BG_ACTIVE, text_color=ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)

        for c, panel in self._panels.items():
            if c == cat:
                panel.pack(fill="both", expand=True)
            else:
                panel.pack_forget()

        # Show/hide overview when switching to/from Page tab
        if hasattr(self.app_ref, 'main_window'):
            overview = self.app_ref.main_window.overview_panel
            if cat == "Page":
                overview.show(extract_mode=True)
            elif overview.is_open:
                overview.hide()

    def update_zoom_label(self, zoom: float):
        self.zoom_label.configure(text=f"{int(zoom * 100)}%")

    def highlight_tool(self, tool_name: str | None):
        for name, btn in self._tool_buttons.items():
            btn.set_active(name == tool_name)

    def _set_tool(self, tool_name: str | None):
        if tool_name is None:
            self.app_ref.active_tool = None
            self.highlight_tool(None)
            if hasattr(self.app_ref, 'main_window') and hasattr(self.app_ref.main_window, 'properties_panel'):
                self.app_ref.main_window.properties_panel.hide()
        else:
            self.app_ref.set_tool(tool_name)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _zoom_in(self):
        vp = self.app_ref.main_window.viewport
        vp.zoom_in()
        self.app_ref.update_status()

    def _zoom_out(self):
        vp = self.app_ref.main_window.viewport
        vp.zoom_out()
        self.app_ref.update_status()

    def _zoom_fit(self):
        vp = self.app_ref.main_window.viewport
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        page = doc.get_page(vp.current_page)
        canvas_w = vp.canvas.winfo_width()
        page_w = page.rect.width * (RENDER_DPI / 72)
        if page_w > 0:
            vp.set_zoom(canvas_w / page_w)
            self.app_ref.update_status()

    def _toggle_overview(self):
        self.app_ref.toggle_overview()

    def _prev_page(self):
        vp = self.app_ref.main_window.viewport
        vp.prev_page()
        self.app_ref.update_status()

    def _next_page(self):
        vp = self.app_ref.main_window.viewport
        vp.next_page()
        self.app_ref.update_status()

    # --- Page management ---

    def _insert_blank(self):
        from app.core.page_operations import insert_blank_page
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        vp = self.app_ref.main_window.viewport
        insert_blank_page(doc.doc, vp.current_page + 1)
        doc.modified = True
        vp.load_document()
        self.app_ref.main_window.sidebar.refresh()

    def _extract_pages(self):
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        overview = self.app_ref.main_window.overview_panel
        overview.show(extract_mode=True)

    def _new_document(self):
        import fitz
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="Untitled.pdf"
        )
        if not path:
            return
        try:
            doc = fitz.open()
            doc.new_page(width=595, height=842)
            doc.save(path)
            doc.close()
            self.app_ref.open_file(path)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to create new PDF:\n{e}")

    def _insert_pages_from_file(self):
        from tkinter import filedialog, messagebox
        from app.core.page_operations import insert_pages_from_file
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Insert Pages", "No document open.")
            return
        path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            vp = self.app_ref.main_window.viewport
            insert_pages_from_file(doc.doc, vp.current_page + 1, path)
            doc.modified = True
            vp.load_document()
            self.app_ref.main_window.sidebar.refresh()
            overview = self.app_ref.main_window.overview_panel
            if overview.is_open:
                overview._render_grid()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to insert pages:\n{e}")

    def _export_as_image(self):
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            from tkinter import messagebox
            messagebox.showinfo("Export", "No document open.")
            return
        from app.ui.dialogs.image_export_dialog import ImageExportDialog
        dlg = ImageExportDialog(self.app_ref)
        self.app_ref.wait_window(dlg)

    def _delete_pages_mode(self):
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        overview = self.app_ref.main_window.overview_panel
        overview.show(extract_mode=True)

    def _rotate_left(self):
        from app.core.page_operations import rotate_page
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        vp = self.app_ref.main_window.viewport
        rotate_page(doc.doc, vp.current_page, -90)
        doc.modified = True
        vp.load_document()
        self.app_ref.main_window.sidebar.refresh()

    def _rotate_right(self):
        from app.core.page_operations import rotate_page
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        vp = self.app_ref.main_window.viewport
        rotate_page(doc.doc, vp.current_page, 90)
        doc.modified = True
        vp.load_document()
        self.app_ref.main_window.sidebar.refresh()

    def _apply_page_range(self):
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        text = self._page_range_var.get().strip()
        if not text:
            return
        pages = self._parse_range_text(text, doc.page_count)
        if pages is None:
            from tkinter import messagebox
            messagebox.showerror("Invalid Range",
                                 f"Could not parse '{text}'.\n"
                                 f"Use format: 1,8,10-12\n"
                                 f"Pages must be between 1 and {doc.page_count}.")
            return
        overview = self.app_ref.main_window.overview_panel
        if not overview.is_open:
            overview.show(extract_mode=True)
        overview._selected_pages = set(pages)
        overview._update_selection_visuals()

    @staticmethod
    def _parse_range_text(text: str, total: int) -> list[int] | None:
        pages = set()
        parts = text.replace(" ", "").split(",")
        for part in parts:
            if not part:
                continue
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    start = int(a) - 1
                    end = int(b) - 1
                    if start < 0 or end >= total or start > end:
                        return None
                    pages.update(range(start, end + 1))
                except ValueError:
                    return None
            else:
                try:
                    p = int(part) - 1
                    if p < 0 or p >= total:
                        return None
                    pages.add(p)
                except ValueError:
                    return None
        return sorted(pages) if pages else None

    # --- Compression ---

    def _compress_document(self):
        from tkinter import messagebox
        from app.core.page_operations import compress_pdf
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Compress", "No document open.")
            return
        if not doc.file_path:
            messagebox.showinfo("Compress", "Save the document first before compressing.")
            return
        try:
            result = compress_pdf(doc.doc, doc.file_path, image_quality=75)
            orig_mb = result["original_bytes"] / (1024 * 1024)
            comp_mb = result["compressed_bytes"] / (1024 * 1024)
            saved = result["saved_pct"]
            path = doc.file_path
            doc.close()
            doc.open(path)
            self.app_ref.main_window.viewport.load_document()
            self.app_ref.main_window.sidebar.refresh()
            self.app_ref.update_status()
            messagebox.showinfo(
                "Compressed",
                f"Original: {orig_mb:.2f} MB\n"
                f"Compressed: {comp_mb:.2f} MB\n"
                f"Saved: {saved}%"
            )
        except Exception as e:
            log_exception(logger, "Compression failed", e)
            messagebox.showerror("Error", f"Compression failed:\n{e}")

    # --- Watermark ---

    def _add_watermark(self):
        from tkinter import messagebox
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Watermark", "No document open.")
            return
        from app.ui.dialogs.watermark_dialog import WatermarkDialog
        dlg = WatermarkDialog(self.app_ref)
        self.app_ref.wait_window(dlg)

    # --- Metadata strip ---

    def _strip_metadata(self):
        from tkinter import messagebox
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Strip Metadata", "No document open.")
            return
        confirm = messagebox.askyesno(
            "Strip Metadata",
            "This will permanently remove ALL metadata from this document:\n\n"
            "\u2022 Title, Author, Subject, Keywords\n"
            "\u2022 Creator, Producer\n"
            "\u2022 Creation / Modification dates\n"
            "\u2022 XMP metadata stream\n\n"
            "Proceed?")
        if not confirm:
            return
        try:
            logger.info("Stripping metadata from %s", doc.file_name)
            d = doc.doc
            d.set_metadata({
                "title": "", "author": "", "subject": "", "keywords": "",
                "creator": "", "producer": "", "creationDate": "", "modDate": "",
            })
            try:
                d.del_xml_metadata()
            except Exception:
                pass
            doc.modified = True
            logger.info("Metadata stripped successfully from %s", doc.file_name)
            messagebox.showinfo("Metadata Stripped",
                                "All metadata has been removed.\nRemember to save the file.")
        except Exception as e:
            log_exception(logger, "Failed to strip metadata", e)
            messagebox.showerror("Error", f"Failed to strip metadata:\n{e}")

    # --- Form Filling ---

    def _toggle_form_fill(self):
        from tkinter import messagebox
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Forms", "No document open.")
            return
        overlay = self.app_ref.main_window.viewport.form_overlay
        if overlay._active:
            overlay.deactivate()
        else:
            overlay.activate()
            if not overlay._active:
                messagebox.showinfo("Forms", "No form fields found in this document.")

    def _save_form_fields(self):
        from tkinter import messagebox
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Forms", "No document open.")
            return
        overlay = self.app_ref.main_window.viewport.form_overlay
        if not overlay._active:
            messagebox.showinfo("Forms", "Form filling is not active.\nClick 'Fill Forms' first.")
            return
        count = overlay.save_values()
        if count > 0:
            messagebox.showinfo("Forms", f"Saved {count} field value(s).\nRemember to save the file.")
        else:
            messagebox.showinfo("Forms", "No field values changed.")

    # --- Password Protection ---

    def _protect_document(self):
        from tkinter import messagebox
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Protect", "No document open.")
            return
        from app.ui.dialogs.password_dialog import PasswordDialog
        dlg = PasswordDialog(self.app_ref)
        self.app_ref.wait_window(dlg)

    # --- Digital Signature ---

    def _sign_document(self):
        from tkinter import messagebox
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Sign", "No document open.")
            return
        from app.ui.sign_dialog import SignDialog
        dlg = SignDialog(self.app_ref, doc)
        self.app_ref.wait_window(dlg)

    # --- Theme Toggle ---

    def _toggle_theme(self):
        """Cycle through dark → light → system → dark."""
        current = self.app_ref.prefs.theme
        cycle = {"dark": "light", "light": "system", "system": "dark"}
        new_theme = cycle.get(current, "dark")
        self.app_ref.set_theme(new_theme)

    # --- About ---

    def _show_about(self):
        from app.ui.about_dialog import AboutDialog
        dlg = AboutDialog(self.app_ref)
        self.app_ref.wait_window(dlg)

    # --- Redaction ---

    # --- OCR ---

    def _run_ocr(self):
        """OCR: if a document is open, OCR it. Otherwise, open an image file
        and convert it to a searchable PDF via ocr_service."""
        from tkinter import messagebox, filedialog
        import threading

        doc = self.app_ref.pdf_doc

        # If a document is already open, use the OCR dialog on the PDF
        if doc and doc.is_open:
            from app.ui.dialogs.ocr_dialog import OCRDialog
            dlg = OCRDialog(self.app_ref, doc)
            self.app_ref.wait_window(dlg)
            return

        # No document open — prompt for an image file to OCR
        try:
            import ocrmypdf  # noqa: F401
        except ImportError:
            messagebox.showerror(
                "OCR",
                "OCRmyPDF is not installed.\n\n"
                "Install with:\n  pip install ocrmypdf\n\n"
                "Tesseract OCR must also be on your system.")
            return

        image_path = filedialog.askopenfilename(
            title="Select image to OCR",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp *.gif"),
                ("All files", "*.*"),
            ])
        if not image_path:
            return

        import os
        from pathlib import Path
        base_name = Path(image_path).stem
        pdf_path = filedialog.asksaveasfilename(
            title="Save searchable PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"{base_name}.pdf")
        if not pdf_path:
            return

        # Run in background thread with indeterminate progress
        import customtkinter as ctk
        progress = ctk.CTkToplevel(self.app_ref)
        progress.title("OCR Processing")
        progress.geometry("340x100")
        progress.resizable(False, False)
        progress.transient(self.app_ref)
        progress.grab_set()

        ctk.CTkLabel(
            progress, text=f"Running OCR on {Path(image_path).name}...",
            font=ctk.CTkFont(family="Courier", size=11)
        ).pack(padx=16, pady=(16, 8))
        bar = ctk.CTkProgressBar(progress, width=280)
        bar.pack(padx=16, pady=4)
        bar.configure(mode="indeterminate")
        bar.start()

        def _convert():
            try:
                from app.core.ocr_service import ocr_image_to_pdf
                ocr_image_to_pdf(image_path, pdf_path)
                self.app_ref.after(0, lambda: _done(None))
            except Exception as e:
                self.app_ref.after(0, lambda err=str(e): _done(err))

        def _done(error):
            bar.stop()
            progress.grab_release()
            progress.destroy()
            if error:
                messagebox.showerror("OCR Error", f"OCR failed:\n\n{error}")
            else:
                self.app_ref.open_file(pdf_path)

        threading.Thread(target=_convert, daemon=True).start()

    # --- Find & Replace ---

    def _find_replace(self):
        from tkinter import messagebox
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Find & Replace", "No document open.")
            return
        from app.ui.dialogs.find_replace_dialog import FindReplaceDialog
        dlg = FindReplaceDialog(self.app_ref, doc)
        self.app_ref.wait_window(dlg)

    def _on_apply_redactions(self):
        self.app_ref.apply_redactions()

    def _on_clear_redactions(self):
        self.app_ref.clear_redactions()
