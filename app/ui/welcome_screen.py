"""Welcome screen when no document is open."""
import customtkinter as ctk
from pathlib import Path
from app.config import (
    BG_DEEP, BG_PANEL, BG_ACTIVE, ACCENT, ACCENT_MUTED,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER_SUBTLE
)


class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(parent, fg_color=BG_DEEP)
        self.app_ref = app_ref

        # center container
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.4, anchor="center")

        title = ctk.CTkLabel(center, text="DocView",
                             font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
                             text_color=TEXT_PRIMARY)
        title.pack(pady=(0, 8))

        subtitle = ctk.CTkLabel(center, text="Standalone PDF editing tool",
                                font=ctk.CTkFont(family="Segoe UI", size=13),
                                text_color=TEXT_SECONDARY)
        subtitle.pack(pady=(0, 6))

        details = ctk.CTkLabel(
            center,
            text="Annotate \u2022 Highlight \u2022 Redact \u2022 OCR \u2022 Edit pages",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED)
        details.pack(pady=(0, 20))

        open_btn = ctk.CTkButton(
            center, text="Open PDF", width=180, height=38,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            text_color="#FFFFFF",
            corner_radius=6,
            command=app_ref.open_file_dialog)
        open_btn.pack(pady=(0, 24))

        # recent files
        self._recent_frame = ctk.CTkFrame(center, fg_color="transparent")
        self._recent_frame.pack(fill="x")

        self.refresh_recent()

    def refresh_recent(self):
        for w in self._recent_frame.winfo_children():
            w.destroy()

        recent = self.app_ref.recent_files.get_all()
        if not recent:
            return

        header = ctk.CTkLabel(self._recent_frame, text="Recent Files",
                              font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                              text_color=TEXT_SECONDARY)
        header.pack(anchor="w", pady=(0, 6))

        for path in recent[:8]:
            name = Path(path).name
            display = name if len(name) <= 50 else name[:47] + "..."
            btn = ctk.CTkButton(
                self._recent_frame, text=display,
                anchor="w", fg_color="transparent",
                hover_color=BG_ACTIVE,
                text_color=TEXT_PRIMARY,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                cursor="hand2",
                command=lambda p=path: self.app_ref.open_file(p))
            btn.pack(fill="x", pady=1)
