"""Properties panel for annotation styling with contextual show/hide."""
import customtkinter as ctk
from app.config import (
    DEFAULT_ANNOT_COLOR, DEFAULT_HIGHLIGHT_COLOR, DEFAULT_TEXT_COLOR,
    DEFAULT_OPACITY, DEFAULT_FONT_SIZE, DEFAULT_BORDER_WIDTH, PROPERTIES_PANEL_WIDTH,
)


class PropertiesPanel(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(parent, width=PROPERTIES_PANEL_WIDTH)
        self.app_ref = app_ref
        self.pack_propagate(False)
        self._visible = False  # start hidden; shown when annotation tool selected

        self.stroke_color = DEFAULT_ANNOT_COLOR
        self.highlight_color = DEFAULT_HIGHLIGHT_COLOR
        self.text_color = DEFAULT_TEXT_COLOR
        self.opacity = DEFAULT_OPACITY
        self.font_size = DEFAULT_FONT_SIZE
        self.border_width = DEFAULT_BORDER_WIDTH

        title = ctk.CTkLabel(self, text="Properties", font=ctk.CTkFont(size=13, weight="bold"))
        title.pack(pady=(10, 5))

        # Color section
        color_frame = ctk.CTkFrame(self, fg_color="transparent")
        color_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(color_frame, text="Stroke Color:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self._color_swatches_frame = ctk.CTkFrame(color_frame, fg_color="transparent")
        self._color_swatches_frame.pack(fill="x", pady=2)

        colors = ["#FF0000", "#00AA00", "#0000FF", "#FF8800", "#8800FF", "#000000", "#FFFF00"]
        for c in colors:
            btn = ctk.CTkButton(
                self._color_swatches_frame, text="", width=22, height=22,
                fg_color=c, hover_color=c,
                command=lambda color=c: self._set_stroke_color(color)
            )
            btn.pack(side="left", padx=1, pady=1)

        # Opacity
        opacity_frame = ctk.CTkFrame(self, fg_color="transparent")
        opacity_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(opacity_frame, text="Opacity:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.opacity_slider = ctk.CTkSlider(opacity_frame, from_=0.1, to=1.0,
                                            command=self._set_opacity)
        self.opacity_slider.set(self.opacity)
        self.opacity_slider.pack(fill="x", pady=2)
        self.opacity_label = ctk.CTkLabel(opacity_frame, text=f"{int(self.opacity * 100)}%",
                                          font=ctk.CTkFont(size=10))
        self.opacity_label.pack(anchor="e")

        # Font size
        font_frame = ctk.CTkFrame(self, fg_color="transparent")
        font_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(font_frame, text="Font Size:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.font_size_var = ctk.StringVar(value=str(self.font_size))
        self.font_size_entry = ctk.CTkEntry(font_frame, textvariable=self.font_size_var, width=60)
        self.font_size_entry.pack(anchor="w", pady=2)
        self.font_size_entry.bind("<Return>", self._on_font_size_change)

        # Border width
        border_frame = ctk.CTkFrame(self, fg_color="transparent")
        border_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(border_frame, text="Border Width:", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.border_slider = ctk.CTkSlider(border_frame, from_=1, to=10,
                                           command=self._set_border_width)
        self.border_slider.set(self.border_width)
        self.border_slider.pack(fill="x", pady=2)
        self.border_label = ctk.CTkLabel(border_frame, text=f"{self.border_width}px",
                                         font=ctk.CTkFont(size=10))
        self.border_label.pack(anchor="e")

    # ── contextual visibility ──

    def show(self):
        if not self._visible:
            self.pack(side="right", fill="y")
            self._visible = True

    def hide(self):
        if self._visible:
            self.pack_forget()
            self._visible = False

    # ── property setters ──

    def _set_stroke_color(self, color: str):
        self.stroke_color = color

    def _set_opacity(self, value: float):
        self.opacity = round(value, 2)
        self.opacity_label.configure(text=f"{int(self.opacity * 100)}%")

    def _set_border_width(self, value: float):
        self.border_width = round(value)
        self.border_label.configure(text=f"{self.border_width}px")

    def _on_font_size_change(self, event=None):
        try:
            self.font_size = int(self.font_size_var.get())
        except ValueError:
            self.font_size_var.set(str(self.font_size))
