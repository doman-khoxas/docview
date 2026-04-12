"""Note list panel — shows pages in the selected section."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLineEdit, QLabel, QMenu
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon
from docnotes.config import NOTE_LIST_WIDTH
from docnotes.core.notebook import Page
from app.ui.theme import TEXT_SECONDARY, TEXT_PRIMARY, BG_SURFACE, BG_HOVER, ACCENT


class NoteList(QWidget):
    """Center-left panel: list of pages in the selected section."""

    note_selected = pyqtSignal(object)          # Page
    new_page_requested = pyqtSignal()
    delete_page_requested = pyqtSignal(object)  # Page
    pin_toggled = pyqtSignal(object)             # Page
    sticky_requested = pyqtSignal()              # New sticky for current section

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(NOTE_LIST_WIDTH)
        self._pages: list[Page] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with section name
        self._header = QLabel("  Select a section")
        self._header.setFixedHeight(28)
        self._header.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        self._header.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            background-color: {BG_SURFACE};
            border-bottom: 1px solid #333;
        """)
        layout.addWidget(self._header)

        # Search filter
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter notes...")
        self._search.setFixedHeight(28)
        self._search.setStyleSheet("border: none; border-bottom: 1px solid #333; padding: 4px 8px;")
        self._search.textChanged.connect(self._apply_filter)
        layout.addWidget(self._search)

        # List
        self._list = QListWidget()
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_context_menu)
        self._list.currentItemChanged.connect(self._on_selection_changed)
        self._list.setStyleSheet(f"""
            QListWidget {{
                border: none;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid #2a2a2a;
            }}
            QListWidget::item:selected {{
                background-color: #264f78;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {BG_HOVER};
            }}
        """)
        layout.addWidget(self._list)

    def load_pages(self, section_name: str, pages: list[Page]):
        """Load pages for the selected section."""
        self._pages = pages
        self._header.setText(f"  {section_name}")
        self._refresh_list()

    def _refresh_list(self):
        self._list.clear()
        filter_text = self._search.text().lower()

        # Sort: pinned first, then by modified descending
        sorted_pages = sorted(self._pages,
                              key=lambda p: (not p.pinned, p.modified or ''),
                              reverse=False)
        # Re-sort: pinned first, then most recent first
        sorted_pages = sorted(sorted_pages,
                              key=lambda p: (0 if p.pinned else 1, -(hash(p.modified) if p.modified else 0)))

        for page in sorted_pages:
            if filter_text and filter_text not in page.name.lower():
                continue

            item = QListWidgetItem()
            prefix = "\U0001f4cc " if page.pinned else ""
            sticky_prefix = "\U0001f4cb " if page.is_sticky else ""
            display = f"{prefix}{sticky_prefix}{page.name}"

            # Add modified date as subtitle
            if page.modified:
                date_str = page.modified[:10] if len(page.modified) >= 10 else page.modified
                display += f"\n{date_str}"

            item.setText(display)
            item.setData(Qt.UserRole, page)
            if page.is_sticky:
                item.setForeground(QColor(ACCENT))
            self._list.addItem(item)

    def _apply_filter(self, text: str):
        self._refresh_list()

    def _on_selection_changed(self, current, previous):
        if current:
            page = current.data(Qt.UserRole)
            if page:
                self.note_selected.emit(page)

    def _show_context_menu(self, pos):
        item = self._list.itemAt(pos)
        menu = QMenu(self)

        menu.addAction("New Page", self.new_page_requested.emit)
        menu.addAction("New Sticky Note", self.sticky_requested.emit)

        if item:
            page = item.data(Qt.UserRole)
            if page:
                menu.addSeparator()
                pin_text = "Unpin" if page.pinned else "Pin to Top"
                menu.addAction(pin_text, lambda: self.pin_toggled.emit(page))
                menu.addSeparator()
                menu.addAction("Delete", lambda: self.delete_page_requested.emit(page))

        menu.exec_(self._list.viewport().mapToGlobal(pos))

    def clear_list(self):
        self._list.clear()
        self._pages.clear()
        self._header.setText("  Select a section")
