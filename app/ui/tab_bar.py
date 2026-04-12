"""Document tab bar with close buttons and modified indicators."""
from PyQt5.QtWidgets import QTabBar
from PyQt5.QtCore import pyqtSignal, Qt
from app.config import TAB_HEIGHT, TAB_MAX_TITLE_LEN


class DocTabBar(QTabBar):
    """Tab bar for open documents with close buttons."""

    tab_switch_requested = pyqtSignal(int)
    tab_close_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setExpanding(False)
        self.setDocumentMode(True)
        self.setElideMode(Qt.ElideRight)
        self.setFixedHeight(TAB_HEIGHT)

        self.currentChanged.connect(self._on_current_changed)
        self.tabCloseRequested.connect(self._on_close_requested)

    def _on_current_changed(self, index):
        if index >= 0:
            self.tab_switch_requested.emit(index)

    def _on_close_requested(self, index):
        self.tab_close_requested.emit(index)

    def refresh_tabs(self, tabs: list):
        """Rebuild tabs from DocumentManager tab list.

        Args:
            tabs: list of TabState objects
        """
        self.blockSignals(True)
        while self.count():
            self.removeTab(0)

        for tab in tabs:
            doc = tab.document
            name = doc.file_name
            if len(name) > TAB_MAX_TITLE_LEN:
                name = name[:TAB_MAX_TITLE_LEN - 3] + "..."
            if doc.modified:
                name = f"\u2022 {name}"
            self.addTab(name)

        self.blockSignals(False)

    def set_active_tab(self, index: int):
        self.blockSignals(True)
        self.setCurrentIndex(index)
        self.blockSignals(False)
