"""Start screen when no document is open — 'Open File' + recent files list."""
import customtkinter as ctk
from pathlib import Path


class WelcomeScreen(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(parent, fg_color=("gray95", "gray14"))
        self.app_ref = app_ref

        # center container
        center = ctk.CTkFrame(self, fg_color="transparent")
        center.place(relx=0.5, rely=0.4, anchor="center")

        title = ctk.CTkLabel(center, text="PDF Editor",
                             font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(pady=(0, 8))

        subtitle = ctk.CTkLabel(center, text="Open a file to get started",
                                font=ctk.CTkFont(size=13),
                                text_color=("gray50", "gray60"))
        subtitle.pack(pady=(0, 20))

        open_btn = ctk.CTkButton(
            center, text="Open PDF", width=180, height=38,
            font=ctk.CTkFont(size=14),
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
                              font=ctk.CTkFont(size=12, weight="bold"))
        header.pack(anchor="w", pady=(0, 6))

        for path in recent[:8]:
            name = Path(path).name
            display = name if len(name) <= 50 else name[:47] + "..."
            btn = ctk.CTkButton(
                self._recent_frame, text=display,
                anchor="w", fg_color="transparent",
                hover_color=("gray85", "gray25"),
                font=ctk.CTkFont(size=11),
                cursor="hand2",
                command=lambda p=path: self.app_ref.open_file(p))
            btn.pack(fill="x", pady=1)
