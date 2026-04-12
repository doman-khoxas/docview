"""Floating sticky note widget."""
import uuid
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QLabel, QPushButton, QSizeGrip
)
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QCursor
from app.config import STICKY_NOTE_WIDTH, STICKY_NOTE_HEIGHT, STICKY_AUTOSAVE_MS
from app.ui.theme import STICKY_COLORS


class StickyNote(QWidget):
    """Frameless floating sticky note with custom title bar."""

    save_requested = pyqtSignal(str)  # note_id
    close_requested = pyqtSignal(str)  # note_id

    def __init__(self, note_id: str | None = None, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.note_id = note_id or str(uuid.uuid4())[:8]
        self._color_name = "yellow"
        self._drag_pos: QPoint | None = None
        self._created = datetime.now().isoformat()
        self._modified = datetime.now().isoformat()

        self.resize(STICKY_NOTE_WIDTH, STICKY_NOTE_HEIGHT)
        self._setup_ui()

        # Auto-save timer
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(STICKY_AUTOSAVE_MS)
        self._save_timer.timeout.connect(lambda: self.save_requested.emit(self.note_id))

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        self._title_bar = QWidget()
        self._title_bar.setFixedHeight(28)
        self._title_bar.setCursor(QCursor(Qt.SizeAllCursor))
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(8, 0, 4, 0)
        title_layout.setSpacing(4)

        self._title_label = QLabel("Sticky Note")
        self._title_label.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        title_layout.addWidget(self._title_label)
        title_layout.addStretch()

        # Color buttons
        for name in ["yellow", "blue", "green", "pink", "orange", "purple"]:
            btn = QPushButton()
            btn.setFixedSize(14, 14)
            btn.setStyleSheet(
                f"background-color: {STICKY_COLORS[name]}; border: 1px solid #999; border-radius: 7px;"
            )
            btn.clicked.connect(lambda _, n=name: self.set_color(n))
            title_layout.addWidget(btn)

        close_btn = QPushButton("\u00d7")
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet(
            "background: transparent; border: none; font-size: 16px; color: #666;"
            "font-weight: bold;"
        )
        close_btn.clicked.connect(lambda: self.close_requested.emit(self.note_id))
        title_layout.addWidget(close_btn)

        layout.addWidget(self._title_bar)

        # Text area
        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont("Segoe UI", 10))
        self._editor.setFrameShape(0)  # No frame
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

        # Size grip
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        layout.addWidget(grip, alignment=Qt.AlignRight)

        self.set_color("yellow")

    def set_color(self, color_name: str):
        self._color_name = color_name
        bg = STICKY_COLORS.get(color_name, STICKY_COLORS["yellow"])
        text_color = "#333333"
        self._title_bar.setStyleSheet(f"background-color: {bg};")
        self._editor.setStyleSheet(
            f"background-color: {bg}; color: {text_color}; border: none; padding: 4px;"
        )
        self.setStyleSheet(f"StickyNote {{ border: 1px solid #aaa; }}")

    @property
    def color_name(self) -> str:
        return self._color_name

    @property
    def text(self) -> str:
        return self._editor.toPlainText()

    @text.setter
    def text(self, value: str):
        self._editor.blockSignals(True)
        self._editor.setPlainText(value)
        self._editor.blockSignals(False)

    @property
    def created(self) -> str:
        return self._created

    @created.setter
    def created(self, value: str):
        self._created = value

    @property
    def note_metadata(self) -> dict:
        return {
            'id': self.note_id,
            'x': self.x(),
            'y': self.y(),
            'width': self.width(),
            'height': self.height(),
            'color': self._color_name,
            'created': self._created,
            'modified': self._modified,
        }

    def _on_text_changed(self):
        self._modified = datetime.now().isoformat()
        self._save_timer.start()

    # ── Dragging ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._title_bar.geometry().contains(event.pos()):
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self.save_requested.emit(self.note_id)
