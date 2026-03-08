"""PDF password/encryption protection dialog."""
import customtkinter as ctk
from tkinter import messagebox
import fitz
from app.config import (
    BG_SURFACE, BG_ABYSS, BG_PANEL, BORDER_SUBTLE,
    ACCENT, ACCENT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)
from app.logger import get_logger

logger = get_logger(__name__)


class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.app_ref = app_ref
        self.title("Protect PDF with Password")
        self.geometry("420x380")
        self.resizable(False, False)
        self.configure(fg_color=BG_SURFACE)

        doc = app_ref.pdf_doc
        if not doc or not doc.is_open:
            self.destroy()
            return

        self._doc = doc

        # Title
        ctk.CTkLabel(
            self, text="Password Protection",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(pady=(16, 12))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=24)

        # User password (to open)
        self._add_label(form, "Open password:")
        self._user_pw = ctk.CTkEntry(
            form, width=260, height=30, show="\u2022",
            fg_color=BG_ABYSS, border_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY, placeholder_text="Password to open PDF",
            font=ctk.CTkFont(family="Segoe UI", size=11))
        self._user_pw.pack(fill="x", pady=(0, 8))

        # Confirm user password
        self._add_label(form, "Confirm open password:")
        self._user_pw2 = ctk.CTkEntry(
            form, width=260, height=30, show="\u2022",
            fg_color=BG_ABYSS, border_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY, placeholder_text="Re-enter password",
            font=ctk.CTkFont(family="Segoe UI", size=11))
        self._user_pw2.pack(fill="x", pady=(0, 8))

        # Owner password (to edit)
        self._add_label(form, "Owner password (optional):")
        self._owner_pw = ctk.CTkEntry(
            form, width=260, height=30, show="\u2022",
            fg_color=BG_ABYSS, border_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY, placeholder_text="Password for editing/printing",
            font=ctk.CTkFont(family="Segoe UI", size=11))
        self._owner_pw.pack(fill="x", pady=(0, 8))

        # Permissions
        perm_frame = ctk.CTkFrame(form, fg_color="transparent")
        perm_frame.pack(fill="x", pady=(4, 0))
        self._print_var = ctk.BooleanVar(value=True)
        self._copy_var = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(
            perm_frame, text="Allow printing", variable=self._print_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_SECONDARY, fg_color=ACCENT,
            hover_color=ACCENT_MUTED, border_color=BORDER_SUBTLE
        ).pack(side="left", padx=(0, 16))

        ctk.CTkCheckBox(
            perm_frame, text="Allow copying text", variable=self._copy_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_SECONDARY, fg_color=ACCENT,
            hover_color=ACCENT_MUTED, border_color=BORDER_SUBTLE
        ).pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(
            btn_frame, text="Protect", width=120, height=32,
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
        user_pw = self._user_pw.get()
        user_pw2 = self._user_pw2.get()
        owner_pw = self._owner_pw.get()

        if not user_pw:
            messagebox.showerror("Error", "Open password cannot be empty.", parent=self)
            return

        if user_pw != user_pw2:
            messagebox.showerror("Error", "Passwords do not match.", parent=self)
            return

        if not owner_pw:
            owner_pw = user_pw

        # Build permissions
        perm = fitz.PDF_PERM_ACCESSIBILITY
        if self._print_var.get():
            perm |= fitz.PDF_PERM_PRINT | fitz.PDF_PERM_PRINT_HQ
        if self._copy_var.get():
            perm |= fitz.PDF_PERM_COPY

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"protected_{self._doc.file_name}",
            parent=self)
        if not path:
            return

        try:
            self._doc.commit_annotations()
            self._doc.doc.save(
                path,
                encryption=fitz.PDF_ENCRYPT_AES_256,
                user_pw=user_pw,
                owner_pw=owner_pw,
                permissions=perm,
                garbage=4,
                deflate=True,
            )
            logger.info("PDF saved with password protection: %s", path)
            messagebox.showinfo(
                "Protected",
                f"Password-protected PDF saved to:\n{path}",
                parent=self)
            self.destroy()
        except Exception as e:
            logger.error("Failed to save protected PDF: %s", e)
            messagebox.showerror("Error", f"Failed to protect PDF:\n{e}", parent=self)
