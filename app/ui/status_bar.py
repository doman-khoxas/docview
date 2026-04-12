"""Status bar with page info, zoom slider, and file info."""
from PyQt5.QtWidgets import (
    QStatusBar, QLabel, QSlider, QWidget, QHBoxLayout, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from app.config import ZOOM_MIN, ZOOM_MAX, ZOOM_DEFAULT


class DocStatusBar(QStatusBar):
    """Status bar with file info, page entry, and zoom control."""

    zoom_requested = pyqtSignal(float)
    page_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # File info (left permanent widget)
        self._file_label = QLabel("")
        self._file_label.setStyleSheet("color: #ffffff; padding: 0 8px;")
        self.addPermanentWidget(self._file_label, 1)

        # Page entry
        page_widget = QWidget()
        page_layout = QHBoxLayout(page_widget)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(4)

        page_label = QLabel("Page")
        page_label.setStyleSheet("color: #ffffff;")
        page_layout.addWidget(page_label)

        self._page_entry = QLineEdit("0")
        self._page_entry.setFixedWidth(40)
        self._page_entry.setAlignment(Qt.AlignCenter)
        self._page_entry.setStyleSheet(
            "background: rgba(255,255,255,0.2); color: #ffffff; "
            "border: 1px solid rgba(255,255,255,0.3); border-radius: 2px; padding: 1px;"
        )
        self._page_entry.returnPressed.connect(self._on_page_entry)
        page_layout.addWidget(self._page_entry)

        self._page_total = QLabel("/ 0")
        self._page_total.setStyleSheet("color: #ffffff;")
        page_layout.addWidget(self._page_total)

        self.addPermanentWidget(page_widget)

        # Zoom slider
        zoom_widget = QWidget()
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(8, 0, 8, 0)
        zoom_layout.setSpacing(4)

        zoom_out_label = QLabel("\u2212")
        zoom_out_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        zoom_layout.addWidget(zoom_out_label)

        self._zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_slider.setRange(int(ZOOM_MIN * 100), int(ZOOM_MAX * 100))
        self._zoom_slider.setValue(int(ZOOM_DEFAULT * 100))
        self._zoom_slider.setFixedWidth(120)
        self._zoom_slider.setStyleSheet(
            "QSlider::groove:horizontal { background: rgba(255,255,255,0.3); height: 3px; border-radius: 1px; }"
            "QSlider::handle:horizontal { background: #ffffff; width: 10px; height: 10px; margin: -4px 0; border-radius: 5px; }"
        )
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider)
        zoom_layout.addWidget(self._zoom_slider)

        zoom_in_label = QLabel("+")
        zoom_in_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        zoom_layout.addWidget(zoom_in_label)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setStyleSheet("color: #ffffff; min-width: 40px;")
        self._zoom_label.setAlignment(Qt.AlignCenter)
        zoom_layout.addWidget(self._zoom_label)

        self.addPermanentWidget(zoom_widget)

    def update_info(self, file_name: str, page: int, total: int, zoom: float):
        self._file_label.setText(file_name)
        self._page_entry.setText(str(page + 1) if total > 0 else "0")
        self._page_total.setText(f"/ {total}")
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(int(zoom * 100))
        self._zoom_slider.blockSignals(False)
        self._zoom_label.setText(f"{int(zoom * 100)}%")

    def _on_zoom_slider(self, value):
        zoom = value / 100.0
        self._zoom_label.setText(f"{value}%")
        self.zoom_requested.emit(zoom)

    def _on_page_entry(self):
        try:
            page = int(self._page_entry.text()) - 1
            self.page_requested.emit(page)
        except ValueError:
            pass
