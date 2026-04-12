"""Search bar with prev/next navigation."""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal
from app.ui.theme import BG_SURFACE, BORDER


class SearchPanel(QWidget):
    """Ctrl+F search bar for PDF text search."""

    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self._results: list[tuple[int, list]] = []
        self._flat_results: list[tuple[int, int]] = []
        self._current_idx = -1
        self._search_callback = None
        self._navigate_callback = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        self._entry = QLineEdit()
        self._entry.setPlaceholderText("Search...")
        self._entry.setFixedWidth(250)
        self._entry.returnPressed.connect(self._do_search)
        layout.addWidget(self._entry)

        find_btn = QPushButton("Find")
        find_btn.setFixedWidth(50)
        find_btn.clicked.connect(self._do_search)
        layout.addWidget(find_btn)

        prev_btn = QPushButton("<")
        prev_btn.setFixedWidth(28)
        prev_btn.clicked.connect(self._prev_result)
        layout.addWidget(prev_btn)

        next_btn = QPushButton(">")
        next_btn.setFixedWidth(28)
        next_btn.clicked.connect(self._next_result)
        layout.addWidget(next_btn)

        self._count_label = QLabel("")
        layout.addWidget(self._count_label)

        layout.addStretch()

        close_btn = QPushButton("\u00d7")
        close_btn.setFixedSize(26, 26)
        close_btn.clicked.connect(self._close)
        layout.addWidget(close_btn)

        self.hide()

    def set_callbacks(self, search_fn, navigate_fn):
        """Set callbacks for search and navigation."""
        self._search_callback = search_fn
        self._navigate_callback = navigate_fn

    def open(self):
        self.show()
        self._entry.setFocus()
        self._entry.selectAll()

    def _close(self):
        self.hide()
        self._results.clear()
        self._flat_results.clear()
        self._current_idx = -1
        self._count_label.setText("")
        self.close_requested.emit()

    @property
    def is_open(self) -> bool:
        return self.isVisible()

    def _do_search(self):
        query = self._entry.text().strip()
        if not query or not self._search_callback:
            return

        self._results = self._search_callback(query)
        self._flat_results.clear()

        for pn, rects in self._results:
            for ri in range(len(rects)):
                self._flat_results.append((pn, ri))

        total = len(self._flat_results)
        if total > 0:
            self._current_idx = 0
            self._navigate_to_current()
        else:
            self._current_idx = -1
            self._count_label.setText("No results")

    def _navigate_to_current(self):
        if not self._flat_results or self._current_idx < 0:
            return
        total = len(self._flat_results)
        page_num, _ = self._flat_results[self._current_idx]
        if self._navigate_callback:
            self._navigate_callback(page_num)
        self._count_label.setText(f"{self._current_idx + 1} / {total}")

    def _next_result(self):
        if not self._flat_results:
            return
        self._current_idx = (self._current_idx + 1) % len(self._flat_results)
        self._navigate_to_current()

    def _prev_result(self):
        if not self._flat_results:
            return
        self._current_idx = (self._current_idx - 1) % len(self._flat_results)
        self._navigate_to_current()
