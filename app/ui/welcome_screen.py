"""Welcome screen shown when no documents are open."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QListWidget,
    QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from pathlib import Path
from app.version import APP_NAME, __version__
from app.ui.theme import ACCENT, TEXT_SECONDARY, BG_SURFACE, BG_HOVER


class WelcomeScreen(QWidget):
    """Start screen with logo, recent files, and quick actions."""

    open_file_requested = pyqtSignal()
    open_recent_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recent_files: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)

        # App name
        title = QLabel(APP_NAME)
        title.setFont(QFont("Segoe UI", 36, QFont.Light))
        title.setStyleSheet(f"color: {ACCENT};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Version
        ver = QLabel(f"v{__version__}")
        ver.setFont(QFont("Segoe UI", 12))
        ver.setStyleSheet(f"color: {TEXT_SECONDARY};")
        ver.setAlignment(Qt.AlignCenter)
        layout.addWidget(ver)

        # Subtitle
        sub = QLabel("PDF Viewer \u2022 Markdown Editor \u2022 Obsidian Integration")
        sub.setFont(QFont("Segoe UI", 11))
        sub.setStyleSheet(f"color: {TEXT_SECONDARY};")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        layout.addSpacing(20)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignCenter)

        open_btn = QPushButton("  Open File")
        open_btn.setFont(QFont("Segoe UI", 11))
        open_btn.setMinimumWidth(160)
        open_btn.setMinimumHeight(36)
        open_btn.setDefault(True)
        open_btn.clicked.connect(self.open_file_requested.emit)
        btn_layout.addWidget(open_btn)

        layout.addLayout(btn_layout)

        layout.addSpacing(16)

        # Recent files
        recent_label = QLabel("Recent Files")
        recent_label.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        recent_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(recent_label)

        self._recent_list = QListWidget()
        self._recent_list.setMaximumWidth(500)
        self._recent_list.setMinimumWidth(400)
        self._recent_list.setMaximumHeight(200)
        self._recent_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BG_SURFACE};
                border: none;
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid #333333;
            }}
            QListWidget::item:hover {{
                background-color: {BG_HOVER};
            }}
        """)
        self._recent_list.itemDoubleClicked.connect(self._on_recent_clicked)
        layout.addWidget(self._recent_list, alignment=Qt.AlignCenter)

        # Keyboard hints
        layout.addSpacing(16)
        hints = QLabel("Ctrl+O  Open File  \u2022  Ctrl+Tab  Switch Tab")
        hints.setFont(QFont("Segoe UI", 9))
        hints.setStyleSheet(f"color: {TEXT_SECONDARY};")
        hints.setAlignment(Qt.AlignCenter)
        layout.addWidget(hints)

    def refresh_recent(self, recent_files: list[str]):
        """Update the recent files list."""
        self._recent_files = recent_files
        self._recent_list.clear()
        for path in recent_files:
            p = Path(path)
            item = QListWidgetItem()
            suffix = p.suffix.upper().lstrip(".")
            item.setText(f"[{suffix}]  {p.name}\n{str(p.parent)}")
            item.setData(Qt.UserRole, path)
            self._recent_list.addItem(item)

        if not recent_files:
            item = QListWidgetItem("No recent files")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            item.setForeground(QColor(TEXT_SECONDARY))
            self._recent_list.addItem(item)

    def _on_recent_clicked(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if path:
            self.open_recent_requested.emit(path)
