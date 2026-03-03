"""About dialog showing version info, features, and changelog."""
import customtkinter as ctk
from app.config import (
    BG_SURFACE, BG_PANEL, BG_DEEP, ACCENT, ACCENT_MUTED,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_DEFAULT,
    BORDER_SUBTLE
)
from app.version import (
    __version__, __build_date__, __codename__, __author__,
    __app_name__, __description__, FEATURES, version_string
)


class AboutDialog(ctk.CTkToplevel):
    """Modal About dialog with version, features, and system info."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title(f"About {__app_name__}")
        self.geometry("400x480")
        self.resizable(False, False)
        self.configure(fg_color=BG_SURFACE)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

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
        # App name + version
        ctk.CTkLabel(
            self, text=__app_name__,
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=ACCENT
        ).pack(pady=(24, 0))

        ctk.CTkLabel(
            self, text=f"v{__version__}  \u2022  {__codename__}",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=TEXT_PRIMARY
        ).pack(pady=(2, 0))

        ctk.CTkLabel(
            self, text=__description__,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_SECONDARY
        ).pack(pady=(4, 0))

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=24, pady=12)

        # Info grid
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=24)

        info_items = [
            ("Build Date", __build_date__),
            ("Author", __author__),
            ("Engine", "PyMuPDF (fitz)"),
            ("UI", "CustomTkinter"),
        ]

        for label, value in info_items:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(
                row, text=f"{label}:", width=90, anchor="e",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=TEXT_MUTED
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=value, anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=TEXT_PRIMARY
            ).pack(side="left", padx=8)

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=BORDER_SUBTLE).pack(
            fill="x", padx=24, pady=12)

        # Features
        ctk.CTkLabel(
            self, text="Features",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", padx=24)

        feat_frame = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=6)
        feat_frame.pack(fill="x", padx=24, pady=(4, 0))

        for feat_name, enabled in FEATURES.items():
            row = ctk.CTkFrame(feat_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=1)
            status = "\u2713" if enabled else "\u2717"
            color = ACCENT if enabled else TEXT_MUTED
            display_name = feat_name.replace("_", " ").title()
            ctk.CTkLabel(
                row, text=f"{status}  {display_name}",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color=color, anchor="w"
            ).pack(side="left")

        # Close button
        ctk.CTkButton(
            self, text="Close", width=100, height=32,
            fg_color=BG_PANEL, hover_color=BG_DEEP,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=4, command=self._close
        ).pack(pady=(16, 16))

    def _close(self):
        self.grab_release()
        self.destroy()
