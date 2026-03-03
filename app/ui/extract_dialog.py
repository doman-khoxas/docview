"""Extract Pages dialog — PDFgear-style with range, mode, and delete options."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import fitz
from app.config import (
    BG_SURFACE, BG_PANEL, BG_DEEP, ACCENT, ACCENT_MUTED, BORDER_SUBTLE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, CORNER_RADIUS, BORDER_DEFAULT,
    COLOR_DANGER
)


class ExtractPagesDialog(ctk.CTkToplevel):
    """
    Modal dialog for extracting pages from the current document.

    Matches PDFgear's Extract Pages dialog:
    - Range: Selected pages / All pages / Custom pages
    - Extract Mode: one PDF / separate PDFs
    - Delete selected pages after extraction checkbox
    """

    def __init__(self, parent, doc, selected_pages: set[int] | None = None):
        super().__init__(parent)
        self.title("Extract Pages")
        self.geometry("440x370")
        self.resizable(False, False)
        self.configure(fg_color=BG_SURFACE)
        self.transient(parent)
        self.grab_set()

        self._doc = doc
        self._selected_pages = sorted(selected_pages) if selected_pages else []
        self._result = None  # Will hold extraction parameters on OK

        self._build_ui()
        self._update_selected_label()

        # Center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        w = self.winfo_width()
        h = self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _build_ui(self):
        pad = {"padx": 20, "pady": (0, 0)}

        # ── Title icon + label ──
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=16, pady=(16, 12))
        ctk.CTkLabel(
            title_frame, text="\u2702  Extract Pages",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        # ── RANGE section ──
        range_frame = ctk.CTkFrame(self, fg_color="transparent")
        range_frame.pack(fill="x", **pad)

        ctk.CTkLabel(
            range_frame, text="Range",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_SECONDARY, width=80, anchor="w"
        ).grid(row=0, column=0, sticky="nw", padx=(0, 12), pady=4)

        # Radio buttons for range
        self._range_var = tk.StringVar(value="selected")

        range_options = ctk.CTkFrame(range_frame, fg_color="transparent")
        range_options.grid(row=0, column=1, sticky="w")

        # Selected pages radio
        sel_row = ctk.CTkFrame(range_options, fg_color="transparent")
        sel_row.pack(fill="x", pady=2)
        ctk.CTkRadioButton(
            sel_row, text="Selected pages",
            variable=self._range_var, value="selected",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED,
            command=self._on_range_change
        ).pack(side="left")
        self._selected_info = ctk.CTkLabel(
            sel_row, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED
        )
        self._selected_info.pack(side="left", padx=8)

        # All pages radio
        ctk.CTkRadioButton(
            range_options, text="All pages",
            variable=self._range_var, value="all",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED,
            command=self._on_range_change
        ).pack(fill="x", pady=2)

        # Custom pages radio + entry
        custom_row = ctk.CTkFrame(range_options, fg_color="transparent")
        custom_row.pack(fill="x", pady=2)
        ctk.CTkRadioButton(
            custom_row, text="Custom pages",
            variable=self._range_var, value="custom",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED,
            command=self._on_range_change
        ).pack(side="left")

        self._custom_var = ctk.StringVar(value="")
        self._custom_entry = ctk.CTkEntry(
            custom_row, textvariable=self._custom_var,
            width=140, height=26,
            fg_color=BG_DEEP, border_color=BORDER_DEFAULT,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4, state="disabled"
        )
        self._custom_entry.pack(side="left", padx=8)

        ctk.CTkLabel(
            range_options, text="eg. 1,8,9-12",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_MUTED
        ).pack(anchor="e", padx=4)

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=20, pady=10)

        # ── EXTRACT MODE section ──
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.pack(fill="x", **pad)

        ctk.CTkLabel(
            mode_frame, text="Extract Mode",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_SECONDARY, width=100, anchor="w"
        ).grid(row=0, column=0, sticky="nw", padx=(0, 12), pady=4)

        mode_options = ctk.CTkFrame(mode_frame, fg_color="transparent")
        mode_options.grid(row=0, column=1, sticky="w")

        self._mode_var = tk.StringVar(value="one_pdf")
        ctk.CTkRadioButton(
            mode_options, text="Extract pages into one PDF",
            variable=self._mode_var, value="one_pdf",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED,
        ).pack(fill="x", pady=2)

        ctk.CTkRadioButton(
            mode_options, text="Extract every page into separate PDFs",
            variable=self._mode_var, value="separate",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED,
        ).pack(fill="x", pady=2)

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=20, pady=10)

        # ── DELETE checkbox ──
        self._delete_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self, text="Delete selected pages after extraction",
            variable=self._delete_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED,
            corner_radius=4
        ).pack(fill="x", padx=20, pady=(0, 12))

        # ── Bottom button bar ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(4, 16))

        ctk.CTkButton(
            btn_frame, text="OK", width=90, height=32,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=4, command=self._on_ok
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Cancel", width=90, height=32,
            fg_color=BG_PANEL, hover_color=BG_DEEP,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=4, command=self._on_cancel
        ).pack(side="right")

    def _update_selected_label(self):
        if self._selected_pages:
            page_str = self._format_page_list(self._selected_pages)
            self._selected_info.configure(
                text=f"  {len(self._selected_pages)} pages selected ({page_str})")
        else:
            self._selected_info.configure(text="  no pages selected")

    def _format_page_list(self, pages: list[int]) -> str:
        """Format page numbers (0-indexed) into human-readable string like '1, 5, 10-12'."""
        if not pages:
            return ""
        display = [p + 1 for p in pages]  # Convert to 1-indexed
        if len(display) <= 5:
            return ", ".join(str(p) for p in display)
        # Abbreviate
        return f"{display[0]}, {display[1]}, ... {display[-1]}"

    def _on_range_change(self):
        if self._range_var.get() == "custom":
            self._custom_entry.configure(state="normal")
        else:
            self._custom_entry.configure(state="disabled")

    def _parse_page_range(self, text: str) -> list[int] | None:
        """Parse 'eg. 1,8,9-12' into 0-indexed page numbers. Returns None on error."""
        pages = set()
        total = self._doc.page_count
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

    def _get_target_pages(self) -> list[int] | None:
        """Resolve which pages to extract based on the range radio selection."""
        mode = self._range_var.get()
        if mode == "selected":
            if not self._selected_pages:
                messagebox.showwarning("No Selection",
                                       "No pages are selected.\nUse 'All pages' or 'Custom pages'.",
                                       parent=self)
                return None
            return self._selected_pages
        elif mode == "all":
            return list(range(self._doc.page_count))
        elif mode == "custom":
            text = self._custom_var.get().strip()
            if not text:
                messagebox.showwarning("Custom Range",
                                       "Please enter a page range (eg. 1,8,9-12).",
                                       parent=self)
                return None
            pages = self._parse_page_range(text)
            if pages is None:
                messagebox.showerror("Invalid Range",
                                     f"Could not parse '{text}'.\n"
                                     f"Use format: 1,8,9-12\n"
                                     f"Pages must be between 1 and {self._doc.page_count}.",
                                     parent=self)
                return None
            return pages
        return None

    def _on_ok(self):
        pages = self._get_target_pages()
        if pages is None:
            return

        extract_mode = self._mode_var.get()
        delete_after = self._delete_var.get()

        if extract_mode == "one_pdf":
            # Save as single PDF
            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"{self._doc.name.replace('.pdf', '')}_extracted.pdf",
                parent=self
            )
            if not path:
                return
            try:
                new_doc = fitz.open()
                for pn in pages:
                    new_doc.insert_pdf(self._doc, from_page=pn, to_page=pn)
                new_doc.save(path)
                new_doc.close()
                page_str = ", ".join(str(p + 1) for p in pages)
                messagebox.showinfo("Extracted",
                                    f"Pages {page_str} saved to:\n{path}",
                                    parent=self)
            except Exception as e:
                messagebox.showerror("Error",
                                     f"Failed to extract pages:\n{e}",
                                     parent=self)
                return

        elif extract_mode == "separate":
            # Choose output directory
            out_dir = filedialog.askdirectory(
                title="Select output folder for separate PDFs",
                parent=self
            )
            if not out_dir:
                return
            try:
                base_name = self._doc.name.replace('.pdf', '')
                for pn in pages:
                    single = fitz.open()
                    single.insert_pdf(self._doc, from_page=pn, to_page=pn)
                    out_path = os.path.join(out_dir, f"{base_name}_page{pn + 1}.pdf")
                    single.save(out_path)
                    single.close()
                messagebox.showinfo("Extracted",
                                    f"{len(pages)} PDF(s) saved to:\n{out_dir}",
                                    parent=self)
            except Exception as e:
                messagebox.showerror("Error",
                                     f"Failed to extract pages:\n{e}",
                                     parent=self)
                return

        # Store result for the caller
        self._result = {
            "pages": pages,
            "delete_after": delete_after,
            "mode": extract_mode,
        }
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        self._result = None
        self.grab_release()
        self.destroy()

    @property
    def result(self):
        return self._result
