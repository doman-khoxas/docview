"""Add text watermark overlay to all pages."""
import fitz
import customtkinter as ctk
from tkinter import messagebox
from app.config import (
    BG_SURFACE, BG_ABYSS, BG_PANEL, BORDER_SUBTLE,
    ACCENT, ACCENT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)
from app.logger import get_logger

logger = get_logger(__name__)


class WatermarkDialog(ctk.CTkToplevel):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.app_ref = app_ref
        self.title("Add Watermark")
        self.geometry("400x340")
        self.resizable(False, False)
        self.configure(fg_color=BG_SURFACE)

        doc = app_ref.pdf_doc
        if not doc or not doc.is_open:
            self.destroy()
            return

        self._doc = doc

        ctk.CTkLabel(
            self, text="Text Watermark",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(pady=(16, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24)

        # Watermark text
        self._add_label(form, "Text:")
        self._text_var = ctk.StringVar(value="CONFIDENTIAL")
        ctk.CTkEntry(
            form, textvariable=self._text_var, width=260, height=30,
            fg_color=BG_ABYSS, border_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12)
        ).pack(fill="x", pady=(0, 8))

        # Font size
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="Size:", width=60, anchor="w",
                     text_color=TEXT_SECONDARY,
                     font=ctk.CTkFont(family="Segoe UI", size=11)).pack(side="left")
        self._size_var = ctk.StringVar(value="48")
        ctk.CTkSegmentedButton(
            row, values=["24", "36", "48", "72"],
            variable=self._size_var, width=200, height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            selected_color=ACCENT, selected_hover_color=ACCENT_MUTED
        ).pack(side="left", padx=4)

        # Opacity
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="Opacity:", width=60, anchor="w",
                     text_color=TEXT_SECONDARY,
                     font=ctk.CTkFont(family="Segoe UI", size=11)).pack(side="left")
        self._opacity_var = ctk.DoubleVar(value=0.3)
        ctk.CTkSlider(
            row, from_=0.05, to=0.8, variable=self._opacity_var,
            width=200, button_color=ACCENT, button_hover_color=ACCENT_MUTED
        ).pack(side="left", padx=4)

        # Color
        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="Color:", width=60, anchor="w",
                     text_color=TEXT_SECONDARY,
                     font=ctk.CTkFont(family="Segoe UI", size=11)).pack(side="left")
        self._color_var = ctk.StringVar(value="gray")
        ctk.CTkSegmentedButton(
            row, values=["gray", "red", "blue"],
            variable=self._color_var, width=200, height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            selected_color=ACCENT, selected_hover_color=ACCENT_MUTED
        ).pack(side="left", padx=4)

        # Diagonal toggle
        self._diagonal_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            form, text="Diagonal placement", variable=self._diagonal_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_SECONDARY, fg_color=ACCENT,
            hover_color=ACCENT_MUTED, border_color=BORDER_SUBTLE
        ).pack(fill="x", pady=(8, 0))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=16)
        ctk.CTkButton(
            btn_frame, text="Apply", width=120, height=32,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self._apply
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            btn_frame, text="Cancel", width=100, height=32,
            fg_color="transparent", hover_color=BG_PANEL,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.destroy
        ).pack(side="left", padx=6)

        self.grab_set()

    def _add_label(self, parent, text):
        ctk.CTkLabel(
            parent, text=text, anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_SECONDARY
        ).pack(fill="x", pady=(4, 2))

    def _apply(self):
        text = self._text_var.get().strip()
        if not text:
            messagebox.showerror("Error", "Watermark text cannot be empty.", parent=self)
            return

        font_size = int(self._size_var.get())
        opacity = self._opacity_var.get()
        diagonal = self._diagonal_var.get()

        color_map = {
            "gray": (0.5, 0.5, 0.5),
            "red": (0.8, 0.2, 0.2),
            "blue": (0.2, 0.2, 0.8),
        }
        color = color_map.get(self._color_var.get(), (0.5, 0.5, 0.5))

        try:
            doc = self._doc.doc
            for page_num in range(doc.page_count):
                page = doc[page_num]
                rect = page.rect
                # Center of page
                cx, cy = rect.width / 2, rect.height / 2
                rotate = 315 if diagonal else 0

                tw = fitz.TextWriter(page.rect)
                font = fitz.Font("helv")
                tw.append(
                    fitz.Point(cx - len(text) * font_size * 0.3, cy),
                    text, font=font, fontsize=font_size
                )
                tw.write_text(page, opacity=opacity, color=color, rotate=rotate)

            self._doc.modified = True
            self.app_ref.main_window.viewport.load_document()
            self.app_ref.update_status()

            logger.info("Watermark '%s' applied to %d pages", text, doc.page_count)
            messagebox.showinfo(
                "Watermark Applied",
                f"Watermark applied to all {doc.page_count} page(s).\n"
                "Remember to save the file.",
                parent=self)
            self.destroy()
        except Exception as e:
            logger.error("Watermark failed: %s", e)
            messagebox.showerror("Error", f"Failed to apply watermark:\n{e}", parent=self)
