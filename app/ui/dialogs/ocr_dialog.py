"""OCR dialog — apply text recognition to scanned PDF pages using ocrmypdf."""
import os
import threading
import tempfile
import shutil
from tkinter import messagebox
import customtkinter as ctk
from app.config import (
    BG_SURFACE, BG_PANEL, BG_DEEP, ACCENT, ACCENT_MUTED, BORDER_SUBTLE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_DEFAULT
)
from app.logger import get_logger

logger = get_logger(__name__)


def _check_ocrmypdf():
    try:
        import ocrmypdf
        return True
    except ImportError:
        return False


class OCRDialog(ctk.CTkToplevel):
    """Dialog for running OCR on PDF pages."""

    def __init__(self, parent, pdf_doc):
        super().__init__(parent)
        self.title("OCR \u2014 Text Recognition")
        self.geometry("440x420")
        self.resizable(False, False)
        self.configure(fg_color=BG_SURFACE)
        self.transient(parent)
        self.grab_set()

        self._parent = parent
        self._pdf_doc = pdf_doc
        self._has_ocrmypdf = _check_ocrmypdf()
        self._running = False

        self._build_ui()

        # Center on parent
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="\u2399  OCR \u2014 Text Recognition",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(padx=16, pady=(16, 8), anchor="w")

        if not self._has_ocrmypdf:
            ctk.CTkLabel(
                self,
                text="OCRmyPDF is not installed.\n\n"
                     "Install with:\n  pip install ocrmypdf\n\n"
                     "Tesseract OCR must also be installed:\n"
                     "  https://github.com/UB-Mannheim/tesseract/wiki",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=TEXT_MUTED, justify="left", wraplength=380
            ).pack(padx=20, pady=20, anchor="w")
            ctk.CTkButton(
                self, text="Close", width=100, height=32,
                fg_color=BG_PANEL, hover_color=BG_DEEP,
                text_color=TEXT_SECONDARY, corner_radius=4,
                command=self._on_cancel
            ).pack(pady=16)
            return

        # Language selection
        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(
            lang_frame, text="OCR Language",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 4))

        self._lang_var = ctk.StringVar(value="eng")
        ctk.CTkOptionMenu(
            lang_frame, variable=self._lang_var,
            values=["eng", "fra", "deu", "spa", "ita", "por", "nld",
                    "jpn", "kor", "chi_sim", "chi_tra", "ara", "rus",
                    "eng+fra", "eng+deu", "eng+spa"],
            width=200, height=28,
            fg_color=BG_DEEP, button_color=BG_PANEL,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        ).pack(anchor="w", pady=2)

        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=20, pady=8)

        # Options
        opts_frame = ctk.CTkFrame(self, fg_color="transparent")
        opts_frame.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(
            opts_frame, text="Options",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 4))

        self._skip_text_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opts_frame, text="Skip pages that already have text",
            variable=self._skip_text_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY, fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED
        ).pack(anchor="w", pady=2)

        self._deskew_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opts_frame, text="Deskew (straighten) pages",
            variable=self._deskew_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY, fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED
        ).pack(anchor="w", pady=2)

        self._clean_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            opts_frame, text="Clean pages before OCR (remove noise)",
            variable=self._clean_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY, fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED
        ).pack(anchor="w", pady=2)

        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=20, pady=8)

        # Progress
        self._progress_label = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED
        )
        self._progress_label.pack(padx=20, anchor="w")

        self._progress_bar = ctk.CTkProgressBar(
            self, width=380, height=8, fg_color=BG_DEEP,
            progress_color=ACCENT, corner_radius=4
        )
        self._progress_bar.pack(padx=20, pady=4)
        self._progress_bar.set(0)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(8, 16))

        self._run_btn = ctk.CTkButton(
            btn_frame, text="Run OCR", width=100, height=32,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=4, command=self._on_run
        )
        self._run_btn.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Cancel", width=100, height=32,
            fg_color=BG_PANEL, hover_color=BG_DEEP,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=4, command=self._on_cancel
        ).pack(side="right")

    def _on_run(self):
        if self._running:
            return
        doc = self._pdf_doc
        if not doc or not doc.file_path:
            messagebox.showinfo("OCR", "Save the document first.", parent=self)
            return

        self._running = True
        self._run_btn.configure(state="disabled", text="Running...")
        self._progress_label.configure(text="Saving document...")
        self._progress_bar.set(0)

        # Save pending changes first
        try:
            doc.save()
        except Exception as e:
            messagebox.showerror("Error",
                                 f"Failed to save before OCR:\n{e}", parent=self)
            self._running = False
            self._run_btn.configure(state="normal", text="Run OCR")
            return

        thread = threading.Thread(target=self._run_ocr, daemon=True)
        thread.start()

    def _run_ocr(self):
        doc = self._pdf_doc
        input_path = doc.file_path
        # Save path before any operations — doc.close() clears _file_path
        saved_path = input_path

        fd, output_path = tempfile.mkstemp(suffix=".pdf",
                                           dir=os.path.dirname(input_path))
        os.close(fd)

        try:
            import ocrmypdf

            self.after(0, lambda: self._progress_label.configure(
                text="Running OCR (this may take a while)..."))
            self.after(0, lambda: self._progress_bar.set(0.2))

            kwargs = {
                "language": self._lang_var.get(),
                "optimize": 1,
                "progress_bar": False,
            }

            if self._skip_text_var.get():
                kwargs["skip_text"] = True
            else:
                kwargs["force_ocr"] = True

            if self._deskew_var.get():
                kwargs["deskew"] = True

            if self._clean_var.get():
                kwargs["clean"] = True

            self.after(0, lambda: self._progress_bar.set(0.3))

            ocrmypdf.ocr(input_path, output_path, **kwargs)

            self.after(0, lambda: self._progress_bar.set(0.8))
            self.after(0, lambda: self._progress_label.configure(
                text="Replacing original file..."))

            # Close document, replace file, reopen
            doc.close()
            shutil.move(output_path, input_path)

            self.after(0, lambda: self._progress_bar.set(1.0))
            self.after(0, lambda p=saved_path: self._on_ocr_success(p))

        except Exception as e:
            logger.error("OCR failed: %s", e)
            if os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except OSError:
                    pass
            self.after(0, lambda err=str(e), p=saved_path: self._on_ocr_error(err, p))

    def _on_ocr_success(self, file_path):
        self._running = False
        self._progress_label.configure(text="OCR complete!")
        self._parent.open_file(file_path)
        messagebox.showinfo("OCR Complete",
                            "Text recognition applied successfully.\n"
                            "The document now contains searchable text.",
                            parent=self)
        self.grab_release()
        self.destroy()

    def _on_ocr_error(self, error_msg, file_path=None):
        self._running = False
        self._run_btn.configure(state="normal", text="Run OCR")
        self._progress_label.configure(text="OCR failed.")
        self._progress_bar.set(0)

        # Try to reopen if document was closed during failed OCR
        doc = self._pdf_doc
        if not doc.is_open and file_path:
            try:
                doc.open(file_path)
                self._parent.main_window.viewport.load_document()
            except Exception:
                pass

        messagebox.showerror("OCR Error",
                             f"OCR processing failed:\n\n{error_msg}",
                             parent=self)

    def _on_cancel(self):
        if self._running:
            return
        self.grab_release()
        self.destroy()
