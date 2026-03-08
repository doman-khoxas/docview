"""Export PDF pages as images (PNG/JPG)."""
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.config import (
    BG_SURFACE, BG_ABYSS, BG_PANEL, BORDER_SUBTLE,
    ACCENT, ACCENT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)
from app.logger import get_logger

logger = get_logger(__name__)


class ImageExportDialog(ctk.CTkToplevel):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.app_ref = app_ref
        self.title("Export Pages as Images")
        self.geometry("400x320")
        self.resizable(False, False)
        self.configure(fg_color=BG_SURFACE)

        doc = app_ref.pdf_doc
        if not doc or not doc.is_open:
            self.destroy()
            return

        self._doc = doc
        self._page_count = doc.page_count
        current = app_ref.main_window.viewport.current_page

        # Title
        ctk.CTkLabel(
            self, text="Export as Image",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(pady=(16, 12))

        # Form
        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24)

        # Page range
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="Pages:", width=80, anchor="w",
                     text_color=TEXT_SECONDARY,
                     font=ctk.CTkFont(family="Segoe UI", size=12)).pack(side="left")
        self._range_var = ctk.StringVar(value=str(current + 1))
        ctk.CTkEntry(row, textvariable=self._range_var, width=180, height=28,
                     fg_color=BG_ABYSS, border_color=BORDER_SUBTLE,
                     text_color=TEXT_PRIMARY, placeholder_text="e.g. 1-5 or 1,3,7",
                     font=ctk.CTkFont(family="Segoe UI", size=11)).pack(side="left", padx=4)

        # Format
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="Format:", width=80, anchor="w",
                     text_color=TEXT_SECONDARY,
                     font=ctk.CTkFont(family="Segoe UI", size=12)).pack(side="left")
        self._format_var = ctk.StringVar(value="PNG")
        ctk.CTkSegmentedButton(
            row, values=["PNG", "JPG"],
            variable=self._format_var, width=180, height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            selected_color=ACCENT, selected_hover_color=ACCENT_MUTED
        ).pack(side="left", padx=4)

        # DPI
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="DPI:", width=80, anchor="w",
                     text_color=TEXT_SECONDARY,
                     font=ctk.CTkFont(family="Segoe UI", size=12)).pack(side="left")
        self._dpi_var = ctk.StringVar(value="150")
        ctk.CTkSegmentedButton(
            row, values=["72", "150", "300"],
            variable=self._dpi_var, width=180, height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            selected_color=ACCENT, selected_hover_color=ACCENT_MUTED
        ).pack(side="left", padx=4)

        # Info
        ctk.CTkLabel(
            self, text=f"Document has {self._page_count} page(s)",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_MUTED
        ).pack(pady=(8, 4))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=16)
        ctk.CTkButton(
            btn_frame, text="Export", width=120, height=32,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._export
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            btn_frame, text="Cancel", width=100, height=32,
            fg_color="transparent", hover_color=BG_PANEL,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.destroy
        ).pack(side="left", padx=6)

        self.grab_set()

    def _parse_pages(self) -> list[int] | None:
        text = self._range_var.get().strip()
        if not text:
            return None
        pages = set()
        for part in text.replace(" ", "").split(","):
            if not part:
                continue
            if "-" in part:
                try:
                    a, b = part.split("-", 1)
                    start, end = int(a) - 1, int(b) - 1
                    if start < 0 or end >= self._page_count or start > end:
                        return None
                    pages.update(range(start, end + 1))
                except ValueError:
                    return None
            else:
                try:
                    p = int(part) - 1
                    if p < 0 or p >= self._page_count:
                        return None
                    pages.add(p)
                except ValueError:
                    return None
        return sorted(pages) if pages else None

    def _export(self):
        pages = self._parse_pages()
        if pages is None:
            messagebox.showerror(
                "Invalid Range",
                f"Could not parse page range.\n"
                f"Use format: 1,3,5-8\n"
                f"Pages must be 1-{self._page_count}.",
                parent=self)
            return

        fmt = self._format_var.get().lower()
        dpi = int(self._dpi_var.get())

        if len(pages) == 1:
            ext = f".{fmt}"
            path = filedialog.asksaveasfilename(
                defaultextension=ext,
                filetypes=[(f"{fmt.upper()} Image", f"*{ext}")],
                initialfile=f"page_{pages[0]+1}{ext}",
                parent=self)
            if not path:
                return
            self._export_page(pages[0], path, dpi, fmt)
            messagebox.showinfo("Exported", f"Page exported to:\n{path}", parent=self)
        else:
            folder = filedialog.askdirectory(title="Select output folder", parent=self)
            if not folder:
                return
            for pn in pages:
                filename = f"page_{pn+1}.{fmt}"
                filepath = os.path.join(folder, filename)
                self._export_page(pn, filepath, dpi, fmt)
            messagebox.showinfo(
                "Exported",
                f"Exported {len(pages)} page(s) to:\n{folder}",
                parent=self)

        logger.info("Exported %d page(s) as %s at %d DPI", len(pages), fmt.upper(), dpi)
        self.destroy()

    def _export_page(self, page_num: int, path: str, dpi: int, fmt: str):
        page = self._doc.get_page(page_num)
        zoom = dpi / 72
        mat = __import__("fitz").Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        if fmt == "jpg":
            pix.save(path, output="jpeg")
        else:
            pix.save(path)
