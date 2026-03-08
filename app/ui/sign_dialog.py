"""Digital Signature dialog — sign PDFs with certificate files, Windows cert store, or stamp.

Supports:
  - PFX / P12 files (PKCS#12) — standard certificate files
  - Windows Certificate Store (CAC / Smart Card via system minidriver)
  - Visible signature stamp (no crypto)

Uses `endesive` for PDF signing (PKCS#7 / CMS).
CAC signing uses Windows CryptoAPI via ctypes for smart card operations.
"""
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import customtkinter as ctk
from app.config import (
    BG_SURFACE, BG_PANEL, BG_DEEP, ACCENT, ACCENT_MUTED, BORDER_SUBTLE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_DEFAULT
)
from app.logger import get_logger, log_exception

logger = get_logger(__name__)


def _check_endesive():
    try:
        import endesive
        return True
    except ImportError:
        return False


def _check_cryptography():
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
        return True
    except ImportError:
        return False


def _check_win_cert_store():
    if sys.platform != "win32":
        return False
    try:
        from app.core.win_cert_store import enumerate_certificates
        return True
    except (ImportError, OSError):
        return False


class SignDialog(ctk.CTkToplevel):
    """Modal dialog for digitally signing the current PDF.

    Three modes:
      1. Certificate file (PFX/P12) — user provides file + password
      2. Windows Certificate Store / CAC — select cert from system store
      3. Visible stamp — text-based signature marker (no crypto)
    """

    def __init__(self, parent, pdf_doc):
        super().__init__(parent)
        self.title("Sign Document")
        self.geometry("500x560")
        self.resizable(False, False)
        self.configure(fg_color=BG_SURFACE)
        self.transient(parent)
        self.grab_set()

        self._parent = parent
        self._pdf_doc = pdf_doc
        self._has_endesive = _check_endesive()
        self._has_crypto = _check_cryptography()
        self._has_win_certs = _check_win_cert_store()
        self._win_certs = []       # list of CertInfo
        self._selected_cert = None  # selected CertInfo

        self._build_ui()

        # Ensure cert contexts are freed even if user clicks X
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Center on parent
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")

    def _build_ui(self):
        # Title
        ctk.CTkLabel(
            self, text="\u270D  Sign Document",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=TEXT_PRIMARY
        ).pack(padx=16, pady=(16, 8), anchor="w")

        # --- Signing mode selection ---
        self._mode_var = tk.StringVar(value="cac" if self._has_win_certs else "pfx")

        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(
            mode_frame, text="Signing Method",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 4))

        # CAC / Windows cert store option (shown first if available)
        if self._has_win_certs:
            ctk.CTkRadioButton(
                mode_frame, text="Smart Card / CAC (Windows Certificate Store)",
                variable=self._mode_var, value="cac",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=TEXT_PRIMARY,
                fg_color=ACCENT, hover_color=ACCENT_MUTED,
                border_color=TEXT_MUTED,
                command=self._on_mode_change
            ).pack(fill="x", pady=2)

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
                     "pip install endesive cryptography",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color=TEXT_MUTED
            ).pack(anchor="w", pady=(4, 0))

        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=20, pady=8)

        # --- Container for mode-specific content ---
        self._content_container = ctk.CTkFrame(self, fg_color="transparent")
        self._content_container.pack(fill="x", padx=20, pady=4)

        # --- CAC section ---
        self._cac_frame = ctk.CTkFrame(self._content_container, fg_color="transparent")
        self._build_cac_section()

        # --- PFX section ---
        self._pfx_frame = ctk.CTkFrame(self._content_container, fg_color="transparent")
        self._build_pfx_section()

        # --- Stamp section ---
        self._stamp_frame = ctk.CTkFrame(self._content_container, fg_color="transparent")
        self._build_stamp_section()

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

        # Show initial mode
        self._on_mode_change()

    def _build_cac_section(self):
        """Build the CAC / Windows Certificate Store UI."""
        ctk.CTkLabel(
            self._cac_frame, text="Select Certificate:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w")

        # Certificate list
        self._cert_listbox_frame = ctk.CTkFrame(
            self._cac_frame, fg_color=BG_DEEP, corner_radius=4,
            border_color=BORDER_DEFAULT, border_width=1)
        self._cert_listbox_frame.pack(fill="x", pady=4)

        self._cert_listbox = tk.Listbox(
            self._cert_listbox_frame, height=5,
            bg="#1a1b1e", fg="#e0e0e0", selectbackground="#4A9EFF",
            selectforeground="#FFFFFF", font=("Segoe UI", 10),
            borderwidth=0, highlightthickness=0, activestyle="none")
        self._cert_listbox.pack(fill="x", padx=2, pady=2)
        self._cert_listbox.bind("<<ListboxSelect>>", self._on_cert_select)

        btn_row = ctk.CTkFrame(self._cac_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=2)

        ctk.CTkButton(
            btn_row, text="Refresh Certificates", width=150, height=28,
            fg_color=BG_PANEL, hover_color=BG_DEEP,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4, command=self._refresh_certs
        ).pack(side="left")

        self._cert_status = ctk.CTkLabel(
            self._cac_frame, text="",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_MUTED
        )
        self._cert_status.pack(anchor="w", pady=(2, 0))

    def _build_pfx_section(self):
        """Build the PFX/P12 certificate file UI."""
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

    def _build_stamp_section(self):
        """Build the visible signature stamp UI."""
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

    # ------------------------------------------------------------------
    # Mode switching
    # ------------------------------------------------------------------

    def _on_mode_change(self):
        mode = self._mode_var.get()
        # Hide all mode frames
        self._cac_frame.pack_forget()
        self._pfx_frame.pack_forget()
        self._stamp_frame.pack_forget()

        if mode == "cac":
            self._cac_frame.pack(in_=self._content_container, fill="x")
            if not self._win_certs:
                self._refresh_certs()
        elif mode == "pfx":
            self._pfx_frame.pack(in_=self._content_container, fill="x")
        else:
            self._stamp_frame.pack(in_=self._content_container, fill="x")

    # ------------------------------------------------------------------
    # CAC certificate management
    # ------------------------------------------------------------------

    def _refresh_certs(self):
        """Enumerate certificates from the Windows certificate store."""
        self._cert_listbox.delete(0, tk.END)
        self._selected_cert = None
        self._cert_status.configure(text="Scanning certificates...")

        try:
            from app.core.win_cert_store import enumerate_certificates
            self._win_certs = enumerate_certificates("MY")

            if not self._win_certs:
                self._cert_status.configure(
                    text="No signing certificates found.\n"
                         "Insert your CAC card and try again.")
                return

            for cert in self._win_certs:
                self._cert_listbox.insert(tk.END, cert.display_name)

            self._cert_status.configure(
                text=f"Found {len(self._win_certs)} certificate(s). "
                     f"Select one to sign with.")

        except Exception as e:
            logger.error("Failed to enumerate certificates: %s", e)
            self._cert_status.configure(
                text=f"Error reading certificates: {e}")

    def _on_cert_select(self, event=None):
        sel = self._cert_listbox.curselection()
        if sel:
            idx = sel[0]
            self._selected_cert = self._win_certs[idx]
            cert = self._selected_cert
            self._cert_status.configure(
                text=f"Selected: {cert.subject}\n"
                     f"Issuer: {cert.issuer}\n"
                     f"Serial: {cert.serial_hex}")

    # ------------------------------------------------------------------
    # PFX helpers
    # ------------------------------------------------------------------

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
        mode = self._sig_page_var.get()
        doc = self._pdf_doc
        if mode == "first":
            return 0
        elif mode == "last":
            return doc.page_count - 1
        else:
            try:
                vp = self._parent.main_window.viewport
                return vp.current_page
            except Exception:
                return doc.page_count - 1

    # ------------------------------------------------------------------
    # Sign dispatch
    # ------------------------------------------------------------------

    def _on_sign(self):
        mode = self._mode_var.get()
        if mode == "cac":
            self._sign_with_cac()
        elif mode == "pfx":
            self._sign_with_cert()
        else:
            self._sign_with_stamp()

    def _sign_with_cac(self):
        """Sign using a certificate from the Windows Certificate Store (CAC)."""
        if not self._selected_cert:
            messagebox.showwarning(
                "Certificate", "Please select a certificate.", parent=self)
            return

        doc = self._pdf_doc
        if not doc.file_path:
            messagebox.showinfo("Sign", "Save the document first.", parent=self)
            return

        # Check if we can use endesive for PDF signature embedding
        if self._has_endesive and self._has_crypto:
            self._sign_cac_with_endesive()
        else:
            self._sign_cac_with_capi()

    def _sign_cac_with_endesive(self):
        """Sign using endesive + Windows CAPI private key proxy."""
        try:
            from endesive.pdf import cms as pdf_cms
            from app.core.win_cert_store import (
                WinCAPIPrivateKey, get_cert_der_bytes
            )
            from cryptography import x509

            cert_info = self._selected_cert
            doc = self._pdf_doc

            # Create CAPI private key proxy
            private_key = WinCAPIPrivateKey(cert_info)

            # Load the certificate using cryptography
            cert_der = get_cert_der_bytes(cert_info)
            certificate = x509.load_der_x509_certificate(cert_der)

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
                "signature": (
                    f"Digitally signed by {cert_info.subject}\n"
                    f"Date: {now.strftime('%Y-%m-%d %H:%M')}"),
                "contact": cert_info.subject,
                "location": "",
                "signingdate": now.strftime("D:%Y%m%d%H%M%S+00'00'"),
                "reason": "Document Signature (CAC)",
            }

            with open(doc.file_path, "rb") as f:
                datau = f.read()

            datas = pdf_cms.sign(
                datau, dct,
                private_key, certificate,
                [],       # no additional chain certs
                "sha256"
            )

            signed_path = doc.file_path.replace(".pdf", "_signed.pdf")
            with open(signed_path, "wb") as f:
                f.write(datau)
                f.write(datas)

            messagebox.showinfo(
                "Signed",
                f"Document signed with CAC certificate!\n\n"
                f"Signer: {cert_info.subject}\n"
                f"Saved to:\n{signed_path}",
                parent=self)

            self.grab_release()
            self.destroy()
            self._parent.open_file(signed_path)

        except Exception as e:
            log_exception(logger, "CAC signing with endesive failed", e)
            messagebox.showerror(
                "Signing Error",
                f"Failed to sign with CAC certificate:\n{e}",
                parent=self)

    def _sign_cac_with_capi(self):
        """Sign using pure Windows CryptoAPI (no endesive needed)."""
        try:
            from app.core.win_cert_store import create_detached_signature
            import fitz

            cert_info = self._selected_cert
            doc = self._pdf_doc
            sig_page = self._get_sig_page()
            now = datetime.now()

            # Save any pending changes
            doc.save()

            # Read PDF bytes
            with open(doc.file_path, "rb") as f:
                pdf_data = f.read()

            # Create the detached CMS/PKCS#7 signature
            signature = create_detached_signature(cert_info, pdf_data)

            # Since we can't embed a proper PDF signature without endesive,
            # add a visible stamp + save the PKCS#7 as an attachment
            page = doc.doc[sig_page]
            rect = page.rect

            sig_w, sig_h = 220, 70
            x0 = rect.width - sig_w - 40
            y0 = rect.height - sig_h - 40
            sig_rect = fitz.Rect(x0, y0, x0 + sig_w, y0 + sig_h)

            shape = page.new_shape()
            shape.draw_rect(sig_rect)
            shape.finish(color=(0.1, 0.3, 0.7), width=2)
            shape.commit()

            stamp_text = (
                f"\u270D Digitally Signed (CAC)\n"
                f"By: {cert_info.subject}\n"
                f"Date: {now.strftime('%Y-%m-%d %H:%M')}\n"
                f"Issuer: {cert_info.issuer}"
            )
            text_rect = fitz.Rect(x0 + 8, y0 + 4, x0 + sig_w - 8, y0 + sig_h - 4)
            page.insert_textbox(
                text_rect, stamp_text,
                fontsize=8, fontname="helv",
                color=(0.1, 0.1, 0.1), align=0)

            # Attach the PKCS#7 signature as an embedded file
            doc.doc.embfile_add(
                "digital_signature.p7s", signature,
                filename="digital_signature.p7s",
                desc="PKCS#7 Digital Signature (CAC)")

            doc.modified = True

            self._parent.main_window.viewport.load_document()
            self._parent.update_status()

            messagebox.showinfo(
                "Signed",
                f"Document signed with CAC certificate.\n\n"
                f"Signer: {cert_info.subject}\n"
                f"PKCS#7 signature attached to document.\n\n"
                f"For full PDF signature embedding, install:\n"
                f"  pip install endesive cryptography\n\n"
                f"Remember to save the file.",
                parent=self)

            self.grab_release()
            self.destroy()

        except Exception as e:
            log_exception(logger, "CAC CAPI signing failed", e)
            messagebox.showerror(
                "Signing Error",
                f"Failed to sign with CAC:\n{e}",
                parent=self)

    def _sign_with_cert(self):
        """Sign using PFX/P12 certificate file with endesive."""
        cert_path = self._cert_path_var.get().strip()
        if not cert_path or not os.path.exists(cert_path):
            messagebox.showwarning(
                "Certificate", "Please select a valid certificate file.",
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

            with open(cert_path, "rb") as f:
                pfx_data = f.read()

            private_key, certificate, chain = pkcs12.load_key_and_certificates(
                pfx_data, password.encode() if password else None,
                default_backend())

            if not private_key or not certificate:
                messagebox.showerror(
                    "Certificate Error",
                    "Could not extract key/certificate from file.",
                    parent=self)
                return

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

            with open(doc.file_path, "rb") as f:
                datau = f.read()

            datas = pdf_cms.sign(
                datau, dct,
                private_key, certificate,
                chain or [],
                "sha256"
            )

            signed_path = doc.file_path.replace(".pdf", "_signed.pdf")
            with open(signed_path, "wb") as f:
                f.write(datau)
                f.write(datas)

            messagebox.showinfo(
                "Signed",
                f"Document signed successfully!\n\nSaved to:\n{signed_path}",
                parent=self)
            self.grab_release()
            self.destroy()
            self._parent.open_file(signed_path)

        except Exception as e:
            log_exception(logger, "PFX signing failed", e)
            messagebox.showerror(
                "Signing Error",
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

            sig_w, sig_h = 200, 60
            x0 = rect.width - sig_w - 40
            y0 = rect.height - sig_h - 40
            sig_rect = fitz.Rect(x0, y0, x0 + sig_w, y0 + sig_h)

            shape = page.new_shape()
            shape.draw_rect(sig_rect)
            shape.finish(color=(0.2, 0.4, 0.8), width=1.5)
            shape.commit()

            stamp_text = (
                f"Signed by: {signer_name}\n"
                f"Reason: {reason}\n"
                f"Date: {now}"
            )
            text_rect = fitz.Rect(x0 + 8, y0 + 6, x0 + sig_w - 8, y0 + sig_h - 6)
            page.insert_textbox(
                text_rect, stamp_text,
                fontsize=9, fontname="helv",
                color=(0.15, 0.15, 0.15), align=0)

            doc.modified = True
            self._parent.main_window.viewport.load_document()
            self._parent.update_status()

            messagebox.showinfo(
                "Stamp Added",
                f"Visible signature stamp added to page {sig_page + 1}.\n"
                f"Remember to save the file.",
                parent=self)
            self.grab_release()
            self.destroy()

        except Exception as e:
            log_exception(logger, "Stamp signing failed", e)
            messagebox.showerror(
                "Error", f"Failed to add signature stamp:\n{e}",
                parent=self)

    def _on_cancel(self):
        # Free any duplicated cert contexts
        if self._win_certs:
            try:
                from app.core.win_cert_store import free_cert_context
                for cert in self._win_certs:
                    free_cert_context(cert)
            except Exception:
                pass
        self.grab_release()
        self.destroy()
