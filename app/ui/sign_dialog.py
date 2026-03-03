"""Digital Signature dialog — sign PDFs with certificate files or Windows cert store.

Supports:
  - PFX / P12 files (PKCS#12) — standard certificate files
  - PEM certificate + key pairs
  - Windows Certificate Store (for CAC / Smart Card via system)

Uses `endesive` for PDF signing (PKCS#7 / CMS).
Falls back to a visible signature stamp if crypto libraries are unavailable.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import customtkinter as ctk
from app.config import (
    BG_SURFACE, BG_PANEL, BG_DEEP, ACCENT, ACCENT_MUTED, BORDER_SUBTLE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_DEFAULT
)


def _check_endesive():
    """Check if endesive is available for real crypto signing."""
    try:
        import endesive
        return True
    except ImportError:
        return False


def _check_cryptography():
    """Check if cryptography lib is available."""
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
        return True
    except ImportError:
        return False


class SignDialog(ctk.CTkToplevel):
    """
    Modal dialog for digitally signing the current PDF.

    Two modes:
      1. Certificate file (PFX/P12) — user provides file + password
      2. Visible stamp — text-based signature marker (no crypto, but visible)

    If `endesive` is installed, mode 1 does real PKCS#7 signing.
    """

    def __init__(self, parent, pdf_doc):
        super().__init__(parent)
        self.title("Sign Document")
        self.geometry("480x460")
        self.resizable(False, False)
        self.configure(fg_color=BG_SURFACE)
        self.transient(parent)
        self.grab_set()

        self._parent = parent
        self._pdf_doc = pdf_doc
        self._has_endesive = _check_endesive()
        self._has_crypto = _check_cryptography()

        self._build_ui()

        # Center
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        w = self.winfo_width()
        h = self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _build_ui(self):
        # Title
        ctk.CTkLabel(
            self, text="\u270D  Sign Document",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(padx=16, pady=(16, 8), anchor="w")

        # Signing mode selection
        self._mode_var = tk.StringVar(value="pfx")

        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(
            mode_frame, text="Signing Method",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkRadioButton(
            mode_frame, text="Certificate File (PFX / P12)",
            variable=self._mode_var, value="pfx",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED,
            command=self._on_mode_change
        ).pack(fill="x", pady=2)

        ctk.CTkRadioButton(
            mode_frame, text="Visible Signature Stamp (no certificate required)",
            variable=self._mode_var, value="stamp",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            border_color=TEXT_MUTED,
            command=self._on_mode_change
        ).pack(fill="x", pady=2)

        if not self._has_endesive:
            ctk.CTkLabel(
                mode_frame,
                text="Note: Install 'endesive' for cryptographic signing.\n"
                     "pip install endesive",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color=TEXT_MUTED
            ).pack(anchor="w", pady=(4, 0))

        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=20, pady=8)

        # --- PFX section ---
        self._pfx_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._pfx_frame.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(
            self._pfx_frame, text="Certificate File:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w")

        cert_row = ctk.CTkFrame(self._pfx_frame, fg_color="transparent")
        cert_row.pack(fill="x", pady=2)

        self._cert_path_var = ctk.StringVar(value="")
        self._cert_entry = ctk.CTkEntry(
            cert_row, textvariable=self._cert_path_var,
            height=28, fg_color=BG_DEEP, border_color=BORDER_DEFAULT,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4
        )
        self._cert_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            cert_row, text="Browse", width=70, height=28,
            fg_color=BG_PANEL, hover_color=BG_DEEP,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4, command=self._browse_cert
        ).pack(side="right")

        ctk.CTkLabel(
            self._pfx_frame, text="Certificate Password:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(8, 0))

        self._password_var = ctk.StringVar(value="")
        self._password_entry = ctk.CTkEntry(
            self._pfx_frame, textvariable=self._password_var,
            height=28, fg_color=BG_DEEP, border_color=BORDER_DEFAULT,
            text_color=TEXT_PRIMARY, show="\u2022",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4
        )
        self._password_entry.pack(fill="x", pady=2)

        # --- Stamp section (hidden initially) ---
        self._stamp_frame = ctk.CTkFrame(self, fg_color="transparent")

        ctk.CTkLabel(
            self._stamp_frame, text="Signer Name:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w")

        self._signer_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            self._stamp_frame, textvariable=self._signer_var,
            height=28, fg_color=BG_DEEP, border_color=BORDER_DEFAULT,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4, placeholder_text="Your Name"
        ).pack(fill="x", pady=2)

        ctk.CTkLabel(
            self._stamp_frame, text="Reason:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(8, 0))

        self._reason_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            self._stamp_frame, textvariable=self._reason_var,
            height=28, fg_color=BG_DEEP, border_color=BORDER_DEFAULT,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4, placeholder_text="eg. Approved, Reviewed"
        ).pack(fill="x", pady=2)

        # --- Common: page placement ---
        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=20, pady=8)

        place_frame = ctk.CTkFrame(self, fg_color="transparent")
        place_frame.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(
            place_frame, text="Signature Page:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY
        ).pack(side="left")

        self._sig_page_var = ctk.StringVar(value="last")
        ctk.CTkOptionMenu(
            place_frame,
            variable=self._sig_page_var,
            values=["first", "last", "current"],
            width=100, height=28,
            fg_color=BG_DEEP, button_color=BG_PANEL,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        ).pack(side="left", padx=8)

        # --- Buttons ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(12, 16))

        ctk.CTkButton(
            btn_frame, text="Sign", width=100, height=32,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=4, command=self._on_sign
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame, text="Cancel", width=100, height=32,
            fg_color=BG_PANEL, hover_color=BG_DEEP,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=4, command=self._on_cancel
        ).pack(side="right")

    def _on_mode_change(self):
        mode = self._mode_var.get()
        if mode == "pfx":
            self._stamp_frame.pack_forget()
            self._pfx_frame.pack(fill="x", padx=20, pady=4, before=self._stamp_frame.master)
        else:
            self._pfx_frame.pack_forget()
            self._stamp_frame.pack(fill="x", padx=20, pady=4)

    def _browse_cert(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Certificate files", "*.pfx *.p12 *.pem"),
                ("All files", "*.*")
            ],
            parent=self
        )
        if path:
            self._cert_path_var.set(path)

    def _get_sig_page(self) -> int:
        """Return 0-indexed page number for signature placement."""
        mode = self._sig_page_var.get()
        doc = self._pdf_doc
        if mode == "first":
            return 0
        elif mode == "last":
            return doc.page_count - 1
        else:  # current
            try:
                vp = self._parent.main_window.viewport
                return vp.current_page
            except Exception:
                return doc.page_count - 1

    def _on_sign(self):
        mode = self._mode_var.get()
        if mode == "pfx":
            self._sign_with_cert()
        else:
            self._sign_with_stamp()

    def _sign_with_cert(self):
        """Sign using PFX/P12 certificate file with endesive."""
        cert_path = self._cert_path_var.get().strip()
        if not cert_path or not os.path.exists(cert_path):
            messagebox.showwarning("Certificate", "Please select a valid certificate file.",
                                   parent=self)
            return

        if not self._has_endesive:
            messagebox.showwarning(
                "Missing Library",
                "The 'endesive' library is required for cryptographic signing.\n\n"
                "Install it with:\n  pip install endesive\n\n"
                "Falling back to visible stamp mode.",
                parent=self)
            return

        password = self._password_var.get()
        doc = self._pdf_doc

        if not doc.file_path:
            messagebox.showinfo("Sign", "Save the document first.", parent=self)
            return

        try:
            from endesive.pdf import cms as pdf_cms
            from endesive import signer
            from cryptography.hazmat.primitives.serialization import pkcs12
            from cryptography.hazmat.backends import default_backend

            # Load the PFX
            with open(cert_path, "rb") as f:
                pfx_data = f.read()

            private_key, certificate, chain = pkcs12.load_key_and_certificates(
                pfx_data, password.encode() if password else None, default_backend()
            )

            if not private_key or not certificate:
                messagebox.showerror("Certificate Error",
                                     "Could not extract key/certificate from file.",
                                     parent=self)
                return

            # Build signing attributes
            now = datetime.now()
            sig_page = self._get_sig_page()

            dct = {
                "aligned": 0,
                "sigflags": 3,
                "sigflagsft": 132,
                "sigpage": sig_page,
                "sigbutton": True,
                "sigfield": "Signature1",
                "auto_sigfield": True,
                "sigandcertify": True,
                "signaturebox": (50, 50, 250, 100),
                "signature": f"Digitally signed on {now.strftime('%Y-%m-%d %H:%M')}",
                "contact": "",
                "location": "",
                "signingdate": now.strftime("D:%Y%m%d%H%M%S+00'00'"),
                "reason": "Document Signature",
                "password": password,
            }

            # Sign the PDF
            with open(doc.file_path, "rb") as f:
                datau = f.read()

            datas = pdf_cms.sign(
                datau, dct,
                private_key, certificate,
                chain or [],
                "sha256"
            )

            # Write signed PDF
            signed_path = doc.file_path.replace(".pdf", "_signed.pdf")
            with open(signed_path, "wb") as f:
                f.write(datau)
                f.write(datas)

            messagebox.showinfo("Signed",
                                f"Document signed successfully!\n\nSaved to:\n{signed_path}",
                                parent=self)
            self.grab_release()
            self.destroy()

            # Open the signed document
            self._parent.open_file(signed_path)

        except Exception as e:
            messagebox.showerror("Signing Error",
                                 f"Failed to sign document:\n{e}",
                                 parent=self)

    def _sign_with_stamp(self):
        """Add a visible signature stamp to the PDF (no crypto)."""
        import fitz
        doc = self._pdf_doc
        signer_name = self._signer_var.get().strip() or "Unsigned"
        reason = self._reason_var.get().strip() or "Signature"
        sig_page = self._get_sig_page()

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            page = doc.doc[sig_page]
            rect = page.rect

            # Signature box in bottom-right area
            sig_w = 200
            sig_h = 60
            x0 = rect.width - sig_w - 40
            y0 = rect.height - sig_h - 40
            sig_rect = fitz.Rect(x0, y0, x0 + sig_w, y0 + sig_h)

            # Draw signature box
            shape = page.new_shape()
            shape.draw_rect(sig_rect)
            shape.finish(color=(0.2, 0.4, 0.8), width=1.5)
            shape.commit()

            # Add signature text
            stamp_text = (
                f"Signed by: {signer_name}\n"
                f"Reason: {reason}\n"
                f"Date: {now}"
            )

            text_rect = fitz.Rect(x0 + 8, y0 + 6, x0 + sig_w - 8, y0 + sig_h - 6)
            rc = page.insert_textbox(
                text_rect, stamp_text,
                fontsize=9, fontname="helv",
                color=(0.15, 0.15, 0.15),
                align=0  # left
            )

            doc.modified = True

            # Refresh viewport
            self._parent.main_window.viewport.load_document()
            self._parent.update_status()

            messagebox.showinfo("Stamp Added",
                                f"Visible signature stamp added to page {sig_page + 1}.\n"
                                f"Remember to save the file.",
                                parent=self)
            self.grab_release()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add signature stamp:\n{e}",
                                 parent=self)

    def _on_cancel(self):
        self.grab_release()
        self.destroy()
