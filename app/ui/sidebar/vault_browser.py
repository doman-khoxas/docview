"""Obsidian vault file browser using QTreeView + QFileSystemModel."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTreeView, QLineEdit, QLabel,
    QFileSystemModel, QMenu, QAction, QApplication
)
from PyQt5.QtCore import Qt, QDir, pyqtSignal, QModelIndex, QSortFilterProxyModel
from PyQt5.QtGui import QFont
from app.ui.theme import TEXT_SECONDARY, BG_SURFACE


class VaultBrowser(QWidget):
    """File browser for Obsidian vault with .md filtering."""

    file_open_requested = pyqtSignal(str)  # absolute file path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vault_path: str | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Search filter
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter notes...")
        self._search.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self._search)

        # File system model
        self._model = QFileSystemModel()
        self._model.setNameFilters(["*.md", "*.markdown"])
        self._model.setNameFilterDisables(False)  # Hide non-matching files
        self._model.setReadOnly(True)

        # Proxy model for filtering
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._proxy.setRecursiveFilteringEnabled(True)

        # Tree view
        self._tree = QTreeView()
        self._tree.setModel(self._proxy)
        self._tree.setHeaderHidden(True)
        # Hide size, type, date columns
        for col in range(1, 4):
            self._tree.hideColumn(col)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        self._tree.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._tree)

        # Status label
        self._status = QLabel("No vault configured")
        self._status.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 10px;")
        layout.addWidget(self._status)

    def set_vault_path(self, path: str):
        """Set the vault root directory."""
        self._vault_path = path
        root_index = self._model.setRootPath(path)
        proxy_index = self._proxy.mapFromSource(root_index)
        self._tree.setRootIndex(proxy_index)
        self._status.setText(f"Vault: {path}")

    def _on_filter_changed(self, text: str):
        self._proxy.setFilterFixedString(text)

    def _on_double_click(self, index: QModelIndex):
        source_index = self._proxy.mapToSource(index)
        path = self._model.filePath(source_index)
        if path and not self._model.isDir(source_index):
            self.file_open_requested.emit(path)

    def _show_context_menu(self, pos):
        index = self._tree.indexAt(pos)
        if not index.isValid():
            return

        source_index = self._proxy.mapToSource(index)
        path = self._model.filePath(source_index)
        is_dir = self._model.isDir(source_index)

        menu = QMenu(self)
        if not is_dir:
            open_action = QAction("Open", menu)
            open_action.triggered.connect(lambda: self.file_open_requested.emit(path))
            menu.addAction(open_action)

            copy_link = QAction("Copy Wikilink", menu)
            from pathlib import Path
            name = Path(path).stem
            copy_link.triggered.connect(lambda: QApplication.clipboard().setText(f"[[{name}]]"))
            menu.addAction(copy_link)

        menu.exec_(self._tree.viewport().mapToGlobal(pos))
