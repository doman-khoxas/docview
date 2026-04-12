"""Signature dialog — draw, type, or upload a signature."""
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QPushButton, QLabel, QLineEdit, QFileDialog, QDialogButtonBox
)
from PyQt5.QtGui import QPainter, QPen, QColor, QImage, QPixmap, QFont, QPainterPath
from PyQt5.QtCore import Qt, QPoint, QSize

SIGNATURES_DIR = Path.home() / ".docview" / "signatures"


class SignatureCanvas(QWidget):
    """Canvas for drawing a signature with the mouse."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 150)
        self._image = QImage(400, 150, QImage.Format_ARGB32)
        self._image.fill(Qt.transparent)
        self._path = QPainterPath()
        self._drawing = False
        self._last_point = QPoint()
        self.setStyleSheet("background: white; border: 1px solid #ccc;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drawing = True
            self._last_point = event.pos()
            self._path.moveTo(event.pos())

    def mouseMoveEvent(self, event):
        if self._drawing:
            painter = QPainter(self._image)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor("#1a1a1a"), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self._last_point, event.pos())
            painter.end()
            self._last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self._drawing = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(0, 0, self._image)
        # Baseline
        painter.setPen(QPen(QColor("#ddd"), 1, Qt.DashLine))
        painter.drawLine(20, 120, 380, 120)
        painter.end()

    def clear(self):
        self._image.fill(Qt.transparent)
        self.update()

    def get_image(self) -> QImage | None:
        """Return the signature image, or None if empty."""
        if self._image.isNull():
            return None
        # Check if anything was drawn
        for y in range(self._image.height()):
            for x in range(self._image.width()):
                if self._image.pixelColor(x, y).alpha() > 0:
                    return self._image
        return None


class SignatureDialog(QDialog):
    """Dialog for creating a signature via draw, type, or upload."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Signature")
        self.setMinimumWidth(450)
        self._result_image: QImage | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Draw tab
        draw_tab = QWidget()
        draw_layout = QVBoxLayout(draw_tab)
        draw_layout.addWidget(QLabel("Draw your signature below:"))
        self._canvas = SignatureCanvas()
        draw_layout.addWidget(self._canvas)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._canvas.clear)
        draw_layout.addWidget(clear_btn, alignment=Qt.AlignRight)
        tabs.addTab(draw_tab, "Draw")

        # Type tab
        type_tab = QWidget()
        type_layout = QVBoxLayout(type_tab)
        type_layout.addWidget(QLabel("Type your name:"))
        self._name_entry = QLineEdit()
        self._name_entry.setFont(QFont("Segoe UI", 14))
        self._name_entry.setPlaceholderText("Your Name")
        self._name_entry.textChanged.connect(self._update_type_preview)
        type_layout.addWidget(self._name_entry)
        self._type_preview = QLabel()
        self._type_preview.setFixedSize(400, 80)
        self._type_preview.setAlignment(Qt.AlignCenter)
        self._type_preview.setStyleSheet("background: white; border: 1px solid #ccc;")
        type_layout.addWidget(self._type_preview)
        tabs.addTab(type_tab, "Type")

        # Upload tab
        upload_tab = QWidget()
        upload_layout = QVBoxLayout(upload_tab)
        upload_layout.addWidget(QLabel("Upload a signature image:"))
        upload_btn = QPushButton("Select Image...")
        upload_btn.clicked.connect(self._upload_image)
        upload_layout.addWidget(upload_btn)
        self._upload_preview = QLabel("No image selected")
        self._upload_preview.setAlignment(Qt.AlignCenter)
        self._upload_preview.setFixedSize(400, 150)
        self._upload_preview.setStyleSheet("background: white; border: 1px solid #ccc;")
        upload_layout.addWidget(self._upload_preview)
        tabs.addTab(upload_tab, "Upload")

        self._tabs = tabs

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_type_preview(self, text):
        if not text:
            self._type_preview.clear()
            return
        img = QImage(400, 80, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.setFont(QFont("Segoe Script", 28))
        p.setPen(QColor("#1a1a1a"))
        p.drawText(img.rect(), Qt.AlignCenter, text)
        p.end()
        self._type_preview.setPixmap(QPixmap.fromImage(img))

    def _upload_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Signature Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)")
        if path:
            img = QImage(path)
            if not img.isNull():
                self._upload_preview.setPixmap(
                    QPixmap.fromImage(img).scaled(
                        400, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self._upload_preview.setProperty("image_path", path)

    def _accept(self):
        tab_idx = self._tabs.currentIndex()
        if tab_idx == 0:  # Draw
            self._result_image = self._canvas.get_image()
        elif tab_idx == 1:  # Type
            text = self._name_entry.text().strip()
            if text:
                img = QImage(400, 80, QImage.Format_ARGB32)
                img.fill(Qt.transparent)
                p = QPainter(img)
                p.setRenderHint(QPainter.Antialiasing)
                p.setFont(QFont("Segoe Script", 28))
                p.setPen(QColor("#1a1a1a"))
                p.drawText(img.rect(), Qt.AlignCenter, text)
                p.end()
                self._result_image = img
        elif tab_idx == 2:  # Upload
            path = self._upload_preview.property("image_path")
            if path:
                self._result_image = QImage(path)

        if self._result_image:
            self._save_signature()
            self.accept()

    def _save_signature(self):
        """Save the signature for reuse."""
        SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)
        path = SIGNATURES_DIR / "last_signature.png"
        self._result_image.save(str(path), "PNG")

    @property
    def signature_image(self) -> QImage | None:
        return self._result_image

    @staticmethod
    def get_last_signature() -> QImage | None:
        """Load the most recently saved signature."""
        path = SIGNATURES_DIR / "last_signature.png"
        if path.exists():
            img = QImage(str(path))
            if not img.isNull():
                return img
        return None
