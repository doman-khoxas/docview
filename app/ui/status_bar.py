"""DocView status bar — file info, page navigation, zoom control."""
import customtkinter as ctk
from app.config import (
    ZOOM_MIN, ZOOM_MAX, BG_ABYSS, BORDER_RED, TEXT_RED, TEXT_MUTED, CORNER_RADIUS,
    ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, BG_SURFACE, BORDER_SUBTLE, ACCENT_MUTED
)

class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(
            parent, height=30,
            fg_color=BG_SURFACE,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=CORNER_RADIUS
        )
        self.app_ref = app_ref
        self.pack_propagate(False)

        # ── left: sidebar toggle + file info ──
        self._sidebar_btn = ctk.CTkButton(
            self, text="\u2630", width=28, height=22,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color="transparent", hover_color=ACCENT_MUTED,
            text_color=TEXT_SECONDARY, corner_radius=4,
            command=self._toggle_sidebar
        )
        self._sidebar_btn.pack(side="left", padx=(6, 2))

        self.file_label = ctk.CTkLabel(
            self, text="No file open", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color=TEXT_SECONDARY
        )
        self.file_label.pack(side="left", padx=4)

        # ── right: zoom slider + zoom % ──
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=6)

        self.zoom_label = ctk.CTkLabel(right, text="100%", width=45, font=ctk.CTkFont(family="Segoe UI", size=12), text_color=TEXT_SECONDARY)
        self.zoom_label.pack(side="right", padx=(4, 0))

        # We style the slider to look harsh and blocky
        self.zoom_slider = ctk.CTkSlider(
            right, from_=int(ZOOM_MIN), to=int(ZOOM_MAX),
            width=120, height=14,
            button_color=ACCENT, button_hover_color="#FFF",
            progress_color=ACCENT_MUTED, fg_color=BG_ABYSS,
            command=self._on_zoom_slider
        )
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(side="right")

        ctk.CTkLabel(right, text="[ZOOM]", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=TEXT_MUTED).pack(side="right", padx=(0, 4))

        # ── center-right: editable page field ──
        page_frame = ctk.CTkFrame(self, fg_color="transparent")
        page_frame.pack(side="right", padx=20)

        self._total_pages = 0
        self.page_var = ctk.StringVar(value="0")
        
        # Blocky MS Paint input box
        self.page_entry = ctk.CTkEntry(
            page_frame, textvariable=self.page_var,
            width=40, height=22,
            fg_color=BG_ABYSS, border_color=BORDER_SUBTLE, text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            justify="center", corner_radius=0
        )
        self.page_entry.pack(side="left")
        self.page_entry.bind("<Return>", self._on_page_entry)

        self.total_label = ctk.CTkLabel(page_frame, text=" / 0", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=TEXT_SECONDARY)
        self.total_label.pack(side="left")

    def update_info(self, file_name: str, page_num: int, page_count: int, zoom: float):
        self.file_label.configure(text=file_name if file_name else "No file open")
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

    def _toggle_sidebar(self):
        if hasattr(self.app_ref, 'main_window'):
            self.app_ref.main_window.sidebar.toggle()

    def _on_page_entry(self, event=None):
        try:
            page = int(self.page_var.get()) - 1
        except ValueError:
            return
        if 0 <= page < self._total_pages:
            self.app_ref.main_window.viewport.go_to_page(page)