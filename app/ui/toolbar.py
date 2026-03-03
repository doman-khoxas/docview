"""Ribbon-style toolbar inspired by PDFgear / Windows 11 Paint."""
import customtkinter as ctk
from app.config import (
    BG_ABYSS, BG_PANEL, BORDER_RED, TEXT_RED,
    HOVER_RED, ACTIVE_RED, TEXT_MUTED, CORNER_RADIUS, RENDER_DPI,
    ACCENT, ACCENT_HOVER, TEXT_PRIMARY, TEXT_SECONDARY, BG_SURFACE,
    BG_ACTIVE, ACCENT_MUTED, BORDER_DEFAULT, BORDER_SUBTLE,
    COLOR_DANGER, BG_HOVER
)

_TAB_CATEGORIES = ["Home", "Edit", "Page", "Tools"]

# Symbol size — large enough to be instantly recognizable
_SYM_SIZE = 20
_LBL_SIZE = 10
_BTN_HEIGHT = 58


class _RibbonButton(ctk.CTkFrame):
    """Compound ribbon button: big symbol on top, small label below."""

    def __init__(self, parent, symbol: str, label: str, command=None,
                 width=64, tool_name=None):
        super().__init__(parent, fg_color="transparent", corner_radius=4,
                         width=width, height=_BTN_HEIGHT,
                         border_width=1, border_color=BG_SURFACE)
        self.pack_propagate(False)
        self._command = command
        self._tool_name = tool_name
        self._default_fg = "transparent"

        self._sym = ctk.CTkLabel(
            self, text=symbol,
            font=ctk.CTkFont(family="Segoe UI Symbol", size=_SYM_SIZE),
            text_color=TEXT_PRIMARY, cursor="hand2"
        )
        self._sym.pack(expand=True, pady=(4, 0))

        self._lbl = ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(family="Segoe UI", size=_LBL_SIZE),
            text_color=TEXT_SECONDARY, cursor="hand2"
        )
        self._lbl.pack(pady=(0, 3))

        # Bind click on the whole widget + children
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

    def _on_leave(self, event=None):
        if self.cget("fg_color") != ACCENT_MUTED:
            self.configure(fg_color=self._default_fg)

    def set_active(self, active: bool):
        if active:
            self.configure(fg_color=ACCENT_MUTED, border_color=ACCENT)
        else:
            self.configure(fg_color="transparent", border_color=BG_SURFACE)
            self._default_fg = "transparent"


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

        # --- Row 1: Tab Strip ---
        self._tab_row = ctk.CTkFrame(self, height=32, fg_color=BG_PANEL, corner_radius=0,
                                      border_width=0)
        self._tab_row.pack(fill="x")
        self._tab_row.pack_propagate(False)

        # Thin accent line between tab strip and ribbon
        ctk.CTkFrame(self, height=1, fg_color=BORDER_DEFAULT, corner_radius=0).pack(fill="x")

        self._cat_buttons: dict[str, ctk.CTkButton] = {}
        for cat in _TAB_CATEGORIES:
            btn = ctk.CTkButton(
                self._tab_row, text=cat, width=80, height=32,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                fg_color="transparent",
                text_color=TEXT_SECONDARY,
                hover_color=BG_ACTIVE,
                corner_radius=0,
                command=lambda c=cat: self._switch_category(c)
            )
            btn.pack(side="left")
            self._cat_buttons[cat] = btn

        # --- Row 2: Ribbon Panel ---
        self._ribbon = ctk.CTkFrame(self, height=86, fg_color=BG_SURFACE, corner_radius=0)
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

    # --- Button factory ---
    def _rb(self, parent, symbol: str, label: str,
            command=None, tool_name=None, width=64) -> _RibbonButton:
        """Create a ribbon button with large symbol + small label."""
        cmd = command if command else (lambda t=tool_name: self._set_tool(t))
        btn = _RibbonButton(parent, symbol, label, command=cmd,
                            width=width, tool_name=tool_name)
        if tool_name is not None:
            self._tool_buttons[tool_name] = btn
        return btn

    def _separator(self, parent):
        """Thin vertical separator line between groups (like PDFgear)."""
        sep = ctk.CTkFrame(parent, width=1, fg_color=BORDER_DEFAULT, corner_radius=0)
        sep.pack(side="left", fill="y", padx=6, pady=8)
        return sep

    def _group(self, parent, title: str) -> ctk.CTkFrame:
        """Tool group with bottom label — no border, clean spacing."""
        outer = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        outer.pack(side="left", padx=2, pady=2, fill="y")

        content = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
        content.pack(side="top", fill="both", expand=True, padx=2, pady=(4, 0))

        ctk.CTkLabel(
            outer, text=title,
            font=ctk.CTkFont(family="Segoe UI", size=9), text_color=TEXT_MUTED
        ).pack(side="bottom", pady=(0, 2))

        return content

    # --- Tab Layouts ---
    def _build_home_panel(self):
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Home"] = p

        # File group
        g_sys = self._group(p, "File")
        self._rb(g_sys, "\u2750", "Open", self.app_ref.open_file_dialog).pack(side="left", padx=1)
        self._rb(g_sys, "\u2913", "Save", self.app_ref.save_file).pack(side="left", padx=1)
        self._rb(g_sys, "\u2912", "Save As", self.app_ref.save_file_as, width=60).pack(side="left", padx=1)
        self._rb(g_sys, "\u2399", "Print", self.app_ref.print_document, width=56).pack(side="left", padx=1)

        self._separator(p)

        # Edit group
        g_edit = self._group(p, "Edit")
        self._rb(g_edit, "\u21B6", "Undo", self.app_ref.undo, width=52).pack(side="left", padx=1)
        self._rb(g_edit, "\u21B7", "Redo", self.app_ref.redo, width=52).pack(side="left", padx=1)

        self._separator(p)

        # View group
        g_view = self._group(p, "View")
        self._rb(g_view, "\u2296", "Out", self._zoom_out, width=48).pack(side="left", padx=1)

        self.zoom_label = ctk.CTkLabel(
            g_view, text="100%", width=48,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self.zoom_label.pack(side="left", padx=2)

        self._rb(g_view, "\u2295", "In", self._zoom_in, width=48).pack(side="left", padx=1)
        self._rb(g_view, "\u2922", "Fit", self._zoom_fit, width=48).pack(side="left", padx=1)

        self._separator(p)

        # Navigate group
        g_nav = self._group(p, "Navigate")
        self._rb(g_nav, "\u25C0", "Prev", self._prev_page, width=48).pack(side="left", padx=1)
        self._rb(g_nav, "\u25B6", "Next", self._next_page, width=48).pack(side="left", padx=1)

        self._separator(p)

        # Mode group
        g_mode = self._group(p, "Mode")
        self._rb(g_mode, "\u2710", "Select", tool_name="select", width=56).pack(side="left", padx=1)
        self._rb(g_mode, "\u270B", "Hand", tool_name="hand", width=56).pack(side="left", padx=1)

        self._separator(p)

        # Info group
        g_info = self._group(p, "Info")
        self._rb(g_info, "\u24D8", "About", command=self._show_about, width=52).pack(side="left", padx=1)

    def _build_edit_panel(self):
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Edit"] = p

        # Draw group
        g_draw = self._group(p, "Draw")
        self._rb(g_draw, "\u270E", "Pen", tool_name="freehand", width=56).pack(side="left", padx=1)
        self._rb(g_draw, "\u2591", "Highlight", tool_name="highlight", width=64).pack(side="left", padx=1)

        self._separator(p)

        # Shapes group
        g_shapes = self._group(p, "Shapes")
        self._rb(g_shapes, "\u25AD", "Rect", tool_name="rect", width=56).pack(side="left", padx=1)
        self._rb(g_shapes, "\u25EF", "Circle", tool_name="circle", width=56).pack(side="left", padx=1)
        self._rb(g_shapes, "\u2571", "Line", tool_name="line", width=56).pack(side="left", padx=1)

        self._separator(p)

        # Text group
        g_text = self._group(p, "Text")
        self._rb(g_text, "A", "Text", tool_name="text", width=56).pack(side="left", padx=1)

        self._separator(p)

        # Insert group
        g_insert = self._group(p, "Insert")
        self._rb(g_insert, "\u2316", "Image", tool_name="image", width=56).pack(side="left", padx=1)

    def _build_page_panel(self):
        """PDFgear-style Page tab: manage pages, extract, delete, rotate, insert."""
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Page"] = p

        # New/Insert group
        g_new = self._group(p, "Insert")
        self._rb(g_new, "\u2795", "New PDF", command=self._new_document, width=64).pack(side="left", padx=1)
        self._rb(g_new, "\u2913", "Insert", command=self._insert_pages_from_file, width=56).pack(side="left", padx=1)
        self._rb(g_new, "\u25A1", "Blank", command=self._insert_blank, width=56).pack(side="left", padx=1)

        self._separator(p)

        # Extract/Delete group
        g_manage = self._group(p, "Manage")
        self._rb(g_manage, "\u2702", "Extract", command=self._extract_pages, width=64).pack(side="left", padx=1)
        self._rb(g_manage, "\u2717", "Delete", command=self._delete_pages_mode, width=56).pack(side="left", padx=1)

        self._separator(p)

        # Rotate group
        g_rot = self._group(p, "Rotate")
        self._rb(g_rot, "\u21BA", "Left", command=self._rotate_left, width=52).pack(side="left", padx=1)
        self._rb(g_rot, "\u21BB", "Right", command=self._rotate_right, width=52).pack(side="left", padx=1)

        self._separator(p)

        # Compress group
        g_compress = self._group(p, "Optimize")
        self._rb(g_compress, "\u2318", "Compress", command=self._compress_document, width=68).pack(side="left", padx=1)

        self._separator(p)

        # Page range input (like PDFgear's "eg.1,8,10-12" field)
        g_range = self._group(p, "Page Range")
        self._page_range_var = ctk.StringVar(value="")
        range_entry = ctk.CTkEntry(
            g_range, textvariable=self._page_range_var,
            width=120, height=28, placeholder_text="eg. 1,8,10-12",
            fg_color=BG_PANEL, border_color=BORDER_DEFAULT,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4
        )
        range_entry.pack(side="left", padx=4, pady=8)
        range_entry.bind("<Return>", lambda e: self._apply_page_range())

        self._rb(g_range, "\u2713", "Apply", command=self._apply_page_range, width=52).pack(side="left", padx=1)

    def _build_tools_panel(self):
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Tools"] = p

        # Redaction group
        g_sec = self._group(p, "Redaction")
        self._rb(g_sec, "\u2588", "Redact", tool_name="redact").pack(side="left", padx=1)
        self._rb(g_sec, "\u2713", "Apply", command=self._on_apply_redactions).pack(side="left", padx=1)
        self._rb(g_sec, "\u2717", "Clear", command=self._on_clear_redactions).pack(side="left", padx=1)

        self._separator(p)

        # Security group
        g_sign = self._group(p, "Security")
        self._rb(g_sign, "\u270D", "Sign", command=self._sign_document, width=56).pack(side="left", padx=1)
        self._rb(g_sign, "\u2327", "Strip\nMeta", command=self._strip_metadata, width=56).pack(side="left", padx=1)

        self._separator(p)

        # OCR group
        g_ocr = self._group(p, "OCR")
        self._rb(g_ocr, "\u2399", "OCR", command=lambda: print("OCR Placeholder")).pack(side="left", padx=1)

    # --- Logic ---
    def _switch_category(self, cat: str):
        if self._active_cat == cat:
            return
        self._active_cat = cat

        for c, btn in self._cat_buttons.items():
            if c == cat:
                btn.configure(fg_color=BG_SURFACE, text_color=ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)

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
        """Highlights the active tool button."""
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
        """Toggle document overview / all-pages view."""
        self.app_ref.toggle_overview()

    # --- Page navigation ---
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
        """Open the overview in extraction/multi-select mode."""
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        overview = self.app_ref.main_window.overview_panel
        overview.show(extract_mode=True)

    # --- Page management methods ---
    def _new_document(self):
        """Create a new blank PDF document."""
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
            doc.new_page(width=595, height=842)  # A4
            doc.save(path)
            doc.close()
            self.app_ref.open_file(path)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to create new PDF:\n{e}")

    def _insert_pages_from_file(self):
        """Insert pages from another PDF into the current document."""
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
            # Re-render overview if open
            overview = self.app_ref.main_window.overview_panel
            if overview.is_open:
                overview._render_grid()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to insert pages:\n{e}")

    def _delete_pages_mode(self):
        """Open overview in extract/delete mode for multi-select deletion."""
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        overview = self.app_ref.main_window.overview_panel
        overview.show(extract_mode=True)

    def _rotate_left(self):
        """Rotate the current page 90° counter-clockwise."""
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
        """Rotate the current page 90° clockwise."""
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
        """Parse the page range field and select those pages in overview."""
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
        # Select those pages in the overview
        overview = self.app_ref.main_window.overview_panel
        if not overview.is_open:
            overview.show(extract_mode=True)
        overview._selected_pages = set(pages)
        overview._update_selection_visuals()

    @staticmethod
    def _parse_range_text(text: str, total: int) -> list[int] | None:
        """Parse '1,8,10-12' into 0-indexed page numbers."""
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
        """Compress the current PDF — downscale images + deflate."""
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

            # Reload the compressed document
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
            messagebox.showerror("Error", f"Compression failed:\n{e}")

    # --- Metadata strip ---
    def _strip_metadata(self):
        """Remove all metadata from the current PDF (OPSEC)."""
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
            d = doc.doc
            # Clear standard PDF metadata
            d.set_metadata({
                "title": "",
                "author": "",
                "subject": "",
                "keywords": "",
                "creator": "",
                "producer": "",
                "creationDate": "",
                "modDate": "",
            })
            # Remove XMP metadata stream
            try:
                d.del_xml_metadata()
            except Exception:
                pass

            doc.modified = True
            messagebox.showinfo("Metadata Stripped",
                                "All metadata has been removed.\n"
                                "Remember to save the file.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to strip metadata:\n{e}")

    # --- Digital Signature ---
    def _sign_document(self):
        """Open the digital signature dialog (CAC / certificate signing)."""
        from tkinter import messagebox
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            messagebox.showinfo("Sign", "No document open.")
            return
        from app.ui.sign_dialog import SignDialog
        dlg = SignDialog(self.app_ref, doc)
        self.app_ref.wait_window(dlg)

    # --- About ---
    def _show_about(self):
        """Show About dialog with version and feature info."""
        from app.ui.about_dialog import AboutDialog
        dlg = AboutDialog(self.app_ref)
        self.app_ref.wait_window(dlg)

    # --- Redaction actions ---
    def _on_apply_redactions(self):
        self.app_ref.apply_redactions()

    def _on_clear_redactions(self):
        self.app_ref.clear_redactions()
