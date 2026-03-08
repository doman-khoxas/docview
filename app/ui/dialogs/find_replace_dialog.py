"""Find & Replace dialog for editing native PDF text content.

Uses PyMuPDF's redaction approach: search for text, redact the region,
and insert replacement text in the same location.
"""
import fitz
from tkinter import messagebox
import customtkinter as ctk
from app.config import (
    BG_SURFACE, BG_PANEL, BG_DEEP, ACCENT, ACCENT_MUTED, BORDER_SUBTLE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_DEFAULT
)
from app.logger import get_logger

logger = get_logger(__name__)


class FindReplaceDialog(ctk.CTkToplevel):
    """Find & Replace dialog for native PDF text editing."""

    def __init__(self, parent, pdf_doc):
        super().__init__(parent)
        self.title("Find & Replace")
        self.geometry("460x340")
        self.resizable(False, False)
        self.configure(fg_color=BG_SURFACE)
        self.transient(parent)
        self.grab_set()

        self._parent = parent
        self._pdf_doc = pdf_doc
        self._matches = []       # [(page_num, fitz.Rect), ...]
        self._current_match = -1

        self._build_ui()

        # Center on parent
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="\u2710  Find & Replace",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(padx=16, pady=(16, 8), anchor="w")

        # Find field
        find_frame = ctk.CTkFrame(self, fg_color="transparent")
        find_frame.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(
            find_frame, text="Find:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY, width=70
        ).pack(side="left")

        self._find_var = ctk.StringVar()
        self._find_entry = ctk.CTkEntry(
            find_frame, textvariable=self._find_var,
            height=28, fg_color=BG_DEEP, border_color=BORDER_DEFAULT,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4
        )
        self._find_entry.pack(side="left", fill="x", expand=True)
        self._find_entry.focus_set()
        self._find_entry.bind("<Return>", lambda e: self._on_find())

        # Replace field
        replace_frame = ctk.CTkFrame(self, fg_color="transparent")
        replace_frame.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(
            replace_frame, text="Replace:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY, width=70
        ).pack(side="left")

        self._replace_var = ctk.StringVar()
        self._replace_entry = ctk.CTkEntry(
            replace_frame, textvariable=self._replace_var,
            height=28, fg_color=BG_DEEP, border_color=BORDER_DEFAULT,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4
        )
        self._replace_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=20, pady=8)

        # Options
        opts_frame = ctk.CTkFrame(self, fg_color="transparent")
        opts_frame.pack(fill="x", padx=20, pady=4)

        self._case_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            opts_frame, text="Case sensitive",
            variable=self._case_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY, fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED
        ).pack(side="left", padx=(0, 16))

        self._scope_var = ctk.StringVar(value="all")
        ctk.CTkLabel(
            opts_frame, text="Scope:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY
        ).pack(side="left")
        ctk.CTkOptionMenu(
            opts_frame, variable=self._scope_var,
            values=["All pages", "Current page"],
            width=130, height=28,
            fg_color=BG_DEEP, button_color=BG_PANEL,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        ).pack(side="left", padx=4)

        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=20, pady=8)

        # Status
        self._status_label = ctk.CTkLabel(
            self, text="Enter text to find.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED
        )
        self._status_label.pack(padx=20, anchor="w")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(12, 16))

        ctk.CTkButton(
            btn_frame, text="Close", width=80, height=32,
            fg_color=BG_PANEL, hover_color=BG_DEEP,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=4, command=self._on_close
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Replace All", width=100, height=32,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=4, command=self._on_replace_all
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Replace", width=80, height=32,
            fg_color=BG_PANEL, hover_color=BG_DEEP,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=4, command=self._on_replace_one
        ).pack(side="right", padx=(8, 0))

        self._next_btn = ctk.CTkButton(
            btn_frame, text="Next", width=70, height=32,
            fg_color=BG_PANEL, hover_color=BG_DEEP,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=4, command=self._on_next
        )
        self._next_btn.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Find", width=70, height=32,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=4, command=self._on_find
        ).pack(side="right")

    def _on_find(self):
        """Search for text in the document."""
        query = self._find_var.get()
        if not query:
            self._status_label.configure(text="Enter text to find.")
            return

        doc = self._pdf_doc
        if not doc or not doc.is_open:
            return

        self._matches.clear()
        self._current_match = -1

        case_sensitive = self._case_var.get()
        flags = 0 if case_sensitive else fitz.TEXT_PRESERVE_WHITESPACE

        if self._scope_var.get() == "Current page":
            pages = [self._parent.main_window.viewport.current_page]
        else:
            pages = range(doc.page_count)

        for pn in pages:
            page = doc.get_page(pn)
            rects = page.search_for(query)
            for r in rects:
                self._matches.append((pn, r))

        if not self._matches:
            self._status_label.configure(text=f"No matches found for '{query}'.")
            vp = self._parent.main_window.viewport
            vp.clear_search_highlights()
        else:
            count = len(self._matches)
            self._status_label.configure(text=f"Found {count} match(es).")
            self._current_match = 0
            self._highlight_matches()
            self._go_to_current_match()

    def _highlight_matches(self):
        """Highlight all matches on the viewport."""
        vp = self._parent.main_window.viewport
        results = {}
        for pn, rect in self._matches:
            results.setdefault(pn, []).append(rect)
        vp.highlight_search_results([(pn, rects) for pn, rects in results.items()])

    def _go_to_current_match(self):
        if 0 <= self._current_match < len(self._matches):
            pn, rect = self._matches[self._current_match]
            vp = self._parent.main_window.viewport
            vp.go_to_page(pn)
            idx = self._current_match + 1
            total = len(self._matches)
            self._status_label.configure(text=f"Match {idx} of {total} (page {pn + 1})")

    def _on_next(self):
        if not self._matches:
            self._on_find()
            return
        self._current_match = (self._current_match + 1) % len(self._matches)
        self._go_to_current_match()

    def _on_replace_one(self):
        """Replace the current match."""
        if not self._matches or self._current_match < 0:
            self._on_find()
            return

        find_text = self._find_var.get()
        replace_text = self._replace_var.get()
        if not find_text:
            return

        pn, rect = self._matches[self._current_match]
        doc = self._pdf_doc

        try:
            page = doc.get_page(pn)
            self._replace_text_in_rect(page, rect, find_text, replace_text)
            doc.modified = True

            # Remove this match and refresh
            self._matches.pop(self._current_match)
            if self._current_match >= len(self._matches):
                self._current_match = 0

            # Refresh viewport
            vp = self._parent.main_window.viewport
            vp.render_current_page()
            self._highlight_matches()

            remaining = len(self._matches)
            self._status_label.configure(
                text=f"Replaced. {remaining} match(es) remaining.")

            if self._matches:
                self._go_to_current_match()

        except Exception as e:
            logger.error("Replace failed: %s", e)
            messagebox.showerror("Replace Error",
                                 f"Failed to replace text:\n{e}", parent=self)

    def _on_replace_all(self):
        """Replace all matches."""
        find_text = self._find_var.get()
        replace_text = self._replace_var.get()
        if not find_text:
            return

        if not self._matches:
            self._on_find()
            if not self._matches:
                return

        count = len(self._matches)
        confirm = messagebox.askyesno(
            "Replace All",
            f"Replace {count} occurrence(s) of '{find_text}'\n"
            f"with '{replace_text}'?",
            parent=self)
        if not confirm:
            return

        doc = self._pdf_doc
        replaced = 0
        # Group by page and process in reverse order to preserve positions
        pages = {}
        for pn, rect in self._matches:
            pages.setdefault(pn, []).append(rect)

        try:
            for pn, rects in pages.items():
                page = doc.get_page(pn)
                for rect in rects:
                    self._replace_text_in_rect(page, rect, find_text, replace_text)
                    replaced += 1
            doc.modified = True

            # Refresh viewport
            vp = self._parent.main_window.viewport
            vp.load_document()

            self._matches.clear()
            self._current_match = -1
            vp.clear_search_highlights()

            self._status_label.configure(
                text=f"Replaced {replaced} occurrence(s).")
            messagebox.showinfo("Replace All",
                                f"Replaced {replaced} occurrence(s).\n"
                                f"Remember to save the file.",
                                parent=self)
        except Exception as e:
            logger.error("Replace all failed: %s", e)
            messagebox.showerror("Error",
                                 f"Replace all failed:\n{e}", parent=self)

    def _replace_text_in_rect(self, page, rect, old_text, new_text):
        """Replace text in a specific rect using redaction approach."""
        # Extract text properties from the region for font matching
        text_dict = page.get_text("dict", clip=rect)
        fontsize = 11
        fontname = "helv"
        text_color = (0, 0, 0)

        # Try to match the original text formatting
        for block in text_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if old_text.lower() in span.get("text", "").lower():
                        fontsize = span.get("size", 11)
                        text_color = span.get("color", 0)
                        # Convert int color to RGB tuple
                        if isinstance(text_color, int):
                            r = ((text_color >> 16) & 0xFF) / 255.0
                            g = ((text_color >> 8) & 0xFF) / 255.0
                            b = (text_color & 0xFF) / 255.0
                            text_color = (r, g, b)
                        break

        # Add redaction annotation and apply it
        page.add_redact_annot(
            rect,
            text=new_text,
            fontsize=fontsize,
            fontname=fontname,
            text_color=text_color,
            fill=(1, 1, 1),  # white background
        )
        page.apply_redactions()

    def _on_close(self):
        # Clear highlights
        try:
            vp = self._parent.main_window.viewport
            vp.clear_search_highlights()
        except Exception:
            pass
        self.grab_release()
        self.destroy()
