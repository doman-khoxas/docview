"""Status bar with zoom slider, editable page number field, and file info."""
import customtkinter as ctk
from app.config import ZOOM_MIN, ZOOM_MAX


class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(parent, height=28, fg_color=("gray88", "gray18"))
        self.app_ref = app_ref
        self.pack_propagate(False)

        # ── left: file name ──
        self.file_label = ctk.CTkLabel(self, text="No file open", anchor="w",
                                       font=ctk.CTkFont(size=11))
        self.file_label.pack(side="left", padx=10)

        # ── right: zoom slider + zoom % ──
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=6)

        self.zoom_label = ctk.CTkLabel(right, text="100%", width=42,
                                       font=ctk.CTkFont(size=11))
        self.zoom_label.pack(side="right", padx=(4, 0))

        self.zoom_slider = ctk.CTkSlider(
            right, from_=ZOOM_MIN, to=ZOOM_MAX,
            width=120, height=14,
            command=self._on_zoom_slider)
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(side="right")

        ctk.CTkLabel(right, text="Zoom:", font=ctk.CTkFont(size=10)).pack(
            side="right", padx=(0, 4))

        # ── center-right: editable page field ──
        page_frame = ctk.CTkFrame(self, fg_color="transparent")
        page_frame.pack(side="right", padx=10)

        self._total_pages = 0
        self.page_var = ctk.StringVar(value="0")
        self.page_entry = ctk.CTkEntry(page_frame, textvariable=self.page_var,
                                       width=40, height=22,
                                       font=ctk.CTkFont(size=11),
                                       justify="center")
        self.page_entry.pack(side="left")
        self.page_entry.bind("<Return>", self._on_page_entry)

        self.total_label = ctk.CTkLabel(page_frame, text=" / 0",
                                        font=ctk.CTkFont(size=11))
        self.total_label.pack(side="left")

    def update_info(self, file_name: str, page_num: int, page_count: int, zoom: float):
        self.file_label.configure(text=file_name or "No file open")
        self._total_pages = page_count
        if page_count > 0:
            self.page_var.set(str(page_num + 1))
            self.total_label.configure(text=f" / {page_count}")
            self.zoom_slider.set(zoom)
            self.zoom_label.configure(text=f"{int(zoom * 100)}%")
        else:
            self.page_var.set("0")
            self.total_label.configure(text=" / 0")
            self.zoom_label.configure(text="")

    def _on_zoom_slider(self, value: float):
        vp = self.app_ref.main_window.viewport
        vp.set_zoom(round(value, 2))
        self.zoom_label.configure(text=f"{int(vp.zoom * 100)}%")
        self.app_ref.update_status()

    def _on_page_entry(self, event=None):
        try:
            page = int(self.page_var.get()) - 1
        except ValueError:
            return
        if 0 <= page < self._total_pages:
            self.app_ref.main_window.viewport.go_to_page(page)
