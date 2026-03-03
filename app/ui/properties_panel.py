"""DocView properties panel — color, opacity, stroke, fill, font controls."""
import customtkinter as ctk
from app.config import (
    DEFAULT_ANNOT_COLOR, DEFAULT_HIGHLIGHT_COLOR, DEFAULT_TEXT_COLOR,
    DEFAULT_OPACITY, DEFAULT_FONT_SIZE, DEFAULT_BORDER_WIDTH, PROPERTIES_PANEL_WIDTH,
    BG_PANEL, BG_ABYSS, BORDER_RED, TEXT_RED, TEXT_MUTED, HOVER_RED, CORNER_RADIUS,
    ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, BG_SURFACE, BORDER_SUBTLE, ACCENT_MUTED,
    BG_DEEP
)

_PALETTE = ["#E1E2E4", "#4A9EFF", "#3BA55C", "#FAA61A", "#ED4245", "#9B59B6", "#000000"]


class PropertiesPanel(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(
            parent, width=PROPERTIES_PANEL_WIDTH,
            fg_color=BG_PANEL,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=CORNER_RADIUS
        )
        self.app_ref = app_ref
        self.pack_propagate(False)
        self._visible = False

        self.stroke_color = DEFAULT_ANNOT_COLOR
        self.fill_color: str | None = None  # None = no fill
        self.highlight_color = DEFAULT_HIGHLIGHT_COLOR
        self.text_color = DEFAULT_TEXT_COLOR
        self.opacity = DEFAULT_OPACITY
        self.font_size = DEFAULT_FONT_SIZE
        self.border_width = DEFAULT_BORDER_WIDTH

        title = ctk.CTkLabel(self, text="Properties", text_color=TEXT_SECONDARY, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        title.pack(pady=(10, 10))

        # --- Stroke color ---
        self._section_label("Stroke Color")
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.pack(fill="x", padx=10, pady=2)
        for c in _PALETTE:
            self._swatch(sf, c, lambda color=c: self._set_stroke_color(color))

        # --- Fill color ---
        self._section_label("Fill Color")
        ff = ctk.CTkFrame(self, fg_color="transparent")
        ff.pack(fill="x", padx=10, pady=2)
        # No-fill button
        ctk.CTkButton(
            ff, text="\u2205", width=24, height=24,
            fg_color=BG_DEEP, hover_color=BG_DEEP, border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=0, text_color=TEXT_MUTED, font=ctk.CTkFont(size=12),
            command=lambda: self._set_fill_color(None)
        ).pack(side="left", padx=1, pady=1)
        for c in _PALETTE:
            self._swatch(ff, c, lambda color=c: self._set_fill_color(color))

        # --- Opacity ---
        self._section_label("Opacity")
        of = ctk.CTkFrame(self, fg_color="transparent")
        of.pack(fill="x", padx=10, pady=2)
        self.opacity_slider = ctk.CTkSlider(
            of, from_=0, to=100,
            button_color=ACCENT, progress_color=ACCENT_MUTED, fg_color=BG_ABYSS,
            command=self._set_opacity
        )
        self.opacity_slider.set(self.opacity * 100)
        self.opacity_slider.pack(fill="x", pady=2)
        self.opacity_label = ctk.CTkLabel(of, text=f"{int(self.opacity * 100)}%", text_color=TEXT_MUTED, font=ctk.CTkFont(family="Segoe UI", size=10))
        self.opacity_label.pack(anchor="e")

        # --- Font size ---
        self._section_label("Font Size")
        ftf = ctk.CTkFrame(self, fg_color="transparent")
        ftf.pack(fill="x", padx=10, pady=2)
        self.font_size_var = ctk.StringVar(value=str(self.font_size))
        self.font_size_entry = ctk.CTkEntry(
            ftf, textvariable=self.font_size_var, width=60,
            fg_color=BG_ABYSS, border_color=BORDER_SUBTLE, text_color=TEXT_PRIMARY, font=ctk.CTkFont(family="Segoe UI"), corner_radius=0
        )
        self.font_size_entry.pack(anchor="w", pady=2)
        self.font_size_entry.bind("<Return>", self._on_font_size_change)

        # --- Stroke width ---
        self._section_label("Stroke Width")
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=10, pady=2)
        self.border_slider = ctk.CTkSlider(
            bf, from_=1, to=10,
            button_color=ACCENT, progress_color=ACCENT_MUTED, fg_color=BG_ABYSS,
            command=self._set_border_width
        )
        self.border_slider.set(self.border_width)
        self.border_slider.pack(fill="x", pady=2)
        self.border_label = ctk.CTkLabel(bf, text=f"{self.border_width}px", text_color=TEXT_MUTED, font=ctk.CTkFont(family="Segoe UI", size=10))
        self.border_label.pack(anchor="e")

    # --- helpers ---
    def _section_label(self, text: str):
        ctk.CTkLabel(self, text=text, text_color=TEXT_SECONDARY,
                     font=ctk.CTkFont(family="Segoe UI", size=11)).pack(anchor="w", padx=10, pady=(8, 0))

    def _swatch(self, parent, color: str, command):
        ctk.CTkButton(
            parent, text="", width=24, height=24,
            fg_color=color, hover_color=color, border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=0, command=command
        ).pack(side="left", padx=1, pady=1)

    def show(self):
        if not self._visible:
            self.pack(side="right", fill="y")
            self._visible = True

    def hide(self):
        if self._visible:
            self.pack_forget()
            self._visible = False

    def _set_stroke_color(self, color: str):
        self.stroke_color = color

    def _set_fill_color(self, color: str | None):
        self.fill_color = color

    def _set_opacity(self, value: float):
        self.opacity = round(value / 100, 2)
        self.opacity_label.configure(text=f"{int(value)}%")

    def _set_border_width(self, value: float):
        self.border_width = round(value)
        self.border_label.configure(text=f"{self.border_width}px")

    def _on_font_size_change(self, event=None):
        try:
            self.font_size = int(self.font_size_var.get())
        except ValueError:
            self.font_size_var.set(str(self.font_size))
