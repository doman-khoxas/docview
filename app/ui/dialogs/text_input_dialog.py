"""Simple text input dialog for freetext annotations."""
import customtkinter as ctk


class TextInputDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Enter Text")
        self.geometry("350x150")
        self.resizable(False, False)
        self.result = None

        ctk.CTkLabel(self, text="Text:").pack(pady=(15, 5))

        self._entry = ctk.CTkEntry(self, width=300)
        self._entry.pack(padx=20)
        self._entry.focus_set()
        self._entry.bind("<Return>", self._on_ok)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="OK", width=80, command=self._on_ok).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", width=80, command=self.destroy).pack(side="left", padx=5)

    def _on_ok(self, event=None):
        text = self._entry.get().strip()
        if text:
            self.result = text
        self.destroy()
