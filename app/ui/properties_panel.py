"""Properties panel for annotation styling."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QLineEdit, QPushButton, QColorDialog, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from app.config import (
    DEFAULT_ANNOT_COLOR, DEFAULT_HIGHLIGHT_COLOR, DEFAULT_TEXT_COLOR,
    DEFAULT_OPACITY, DEFAULT_FONT_SIZE, DEFAULT_BORDER_WIDTH, PROPERTIES_PANEL_WIDTH,
)
from app.ui.theme import BG_SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY


class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(PROPERTIES_PANEL_WIDTH)

        self.stroke_color = DEFAULT_ANNOT_COLOR
        self.highlight_color = DEFAULT_HIGHLIGHT_COLOR
        self.text_color = DEFAULT_TEXT_COLOR
        self.opacity = DEFAULT_OPACITY
        self.font_size = DEFAULT_FONT_SIZE
        self.border_width = DEFAULT_BORDER_WIDTH

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Title
        title = QLabel("Properties")
        title.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        layout.addWidget(title)

        # Stroke color
        layout.addWidget(QLabel("Stroke Color"))
        color_row = QHBoxLayout()
        color_row.setSpacing(2)
        colors = ["#FF0000", "#00AA00", "#0000FF", "#FF8800", "#8800FF", "#000000", "#FFFF00"]
        for c in colors:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"background-color: {c}; border: 1px solid {BORDER}; border-radius: 2px;")
            btn.clicked.connect(lambda _, color=c: self._set_stroke_color(color))
            color_row.addWidget(btn)
        color_row.addStretch()
        layout.addLayout(color_row)

        # Custom color button
        custom_btn = QPushButton("Custom...")
        custom_btn.setFixedHeight(24)
        custom_btn.clicked.connect(self._pick_color)
        layout.addWidget(custom_btn)

        # Opacity
        layout.addWidget(QLabel("Opacity"))
        opacity_row = QHBoxLayout()
        self._opacity_slider = QSlider(Qt.Horizontal)
        self._opacity_slider.setRange(10, 100)
        self._opacity_slider.setValue(int(self.opacity * 100))
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self._opacity_slider)
        self._opacity_label = QLabel(f"{int(self.opacity * 100)}%")
        self._opacity_label.setFixedWidth(36)
        opacity_row.addWidget(self._opacity_label)
        layout.addLayout(opacity_row)

        # Font size
        layout.addWidget(QLabel("Font Size"))
        self._font_entry = QLineEdit(str(self.font_size))
        self._font_entry.setFixedWidth(60)
        self._font_entry.returnPressed.connect(self._on_font_change)
        layout.addWidget(self._font_entry)

        # Border width
        layout.addWidget(QLabel("Border Width"))
        border_row = QHBoxLayout()
        self._border_slider = QSlider(Qt.Horizontal)
        self._border_slider.setRange(1, 10)
        self._border_slider.setValue(self.border_width)
        self._border_slider.valueChanged.connect(self._on_border_changed)
        border_row.addWidget(self._border_slider)
        self._border_label = QLabel(f"{self.border_width}px")
        self._border_label.setFixedWidth(36)
        border_row.addWidget(self._border_label)
        layout.addLayout(border_row)

        layout.addStretch()

    def _set_stroke_color(self, color: str):
        self.stroke_color = color

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self.stroke_color), self, "Pick Color")
        if color.isValid():
            self.stroke_color = color.name()

    def _on_opacity_changed(self, value):
        self.opacity = value / 100.0
        self._opacity_label.setText(f"{value}%")

    def _on_font_change(self):
        try:
            self.font_size = int(self._font_entry.text())
        except ValueError:
            self._font_entry.setText(str(self.font_size))

    def _on_border_changed(self, value):
        self.border_width = value
        self._border_label.setText(f"{value}px")
