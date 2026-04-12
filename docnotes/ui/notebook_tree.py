"""Notebook/Section tree panel."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QMenu,
    QInputDialog, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap, QPainter, QBrush
from docnotes.config import NOTEBOOK_TREE_WIDTH
from app.ui.theme import TEXT_SECONDARY, BG_SURFACE, ACCENT


def _color_icon(color: str, size: int = 14) -> QIcon:
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(1, 1, size - 2, size - 2, 3, 3)
    p.end()
    return QIcon(pix)


class NotebookTree(QWidget):
    """Left panel: tree of Notebooks → Sections."""

    section_selected = pyqtSignal(object, object)  # (notebook, section)
    notebook_selected = pyqtSignal(object)          # notebook
    create_notebook_requested = pyqtSignal()
    create_section_requested = pyqtSignal(object)   # notebook
    delete_notebook_requested = pyqtSignal(object)
    delete_section_requested = pyqtSignal(object, object)
    rename_requested = pyqtSignal(object, str)       # item, new_name
    sticky_requested = pyqtSignal(str)               # section_path for new sticky

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(NOTEBOOK_TREE_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("  NOTEBOOKS")
        header.setFixedHeight(28)
        header.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        header.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            background-color: {BG_SURFACE};
            border-bottom: 1px solid #333;
            padding-left: 8px;
        """)
        layout.addWidget(header)

        # Tree
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.setStyleSheet("""
            QTreeWidget { border: none; }
            QTreeWidget::item { padding: 4px 0; }
        """)
        layout.addWidget(self._tree)

        self._notebooks = []
        self._section_map: dict[int, tuple] = {}  # item_id → (notebook, section)

    def load_vault(self, notebooks: list):
        """Populate tree from vault notebooks."""
        self._tree.clear()
        self._notebooks = notebooks
        self._section_map.clear()

        for nb in notebooks:
            nb_item = QTreeWidgetItem([nb.name])
            nb_item.setIcon(0, _color_icon(nb.color))
            nb_item.setFont(0, QFont("Segoe UI", 10, QFont.DemiBold))
            nb_item.setData(0, Qt.UserRole, ('notebook', nb))
            nb_item.setExpanded(True)
            self._tree.addTopLevelItem(nb_item)

            for sec in nb.sections:
                sec_item = QTreeWidgetItem([f"  {sec.name}  ({sec.page_count})"])
                sec_item.setData(0, Qt.UserRole, ('section', nb, sec))
                nb_item.addChild(sec_item)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        if data[0] == 'notebook':
            self.notebook_selected.emit(data[1])
        elif data[0] == 'section':
            self.section_selected.emit(data[1], data[2])

    def _show_context_menu(self, pos):
        item = self._tree.itemAt(pos)
        menu = QMenu(self)

        if item:
            data = item.data(0, Qt.UserRole)
            if data and data[0] == 'notebook':
                nb = data[1]
                menu.addAction("New Section", lambda: self.create_section_requested.emit(nb))
                menu.addSeparator()
                menu.addAction("New Sticky Note", lambda: self.sticky_requested.emit(nb.name + "/"))
                menu.addSeparator()
                menu.addAction("Rename Notebook", lambda: self._rename_item(item, nb))
                menu.addAction("Delete Notebook", lambda: self.delete_notebook_requested.emit(nb))
            elif data and data[0] == 'section':
                nb, sec = data[1], data[2]
                menu.addAction("New Page", lambda: self.section_selected.emit(nb, sec))
                menu.addAction("New Sticky Note", lambda: self.sticky_requested.emit(f"{nb.name}/{sec.name}"))
                menu.addSeparator()
                menu.addAction("Delete Section", lambda: self.delete_section_requested.emit(nb, sec))
        else:
            menu.addAction("New Notebook", self.create_notebook_requested.emit)
            menu.addSeparator()
            menu.addAction("New Sticky Note", lambda: self.sticky_requested.emit(""))

        menu.exec_(self._tree.viewport().mapToGlobal(pos))

    def _rename_item(self, item, obj):
        old_name = obj.name
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=old_name)
        if ok and new_name.strip() and new_name != old_name:
            self.rename_requested.emit(obj, new_name.strip())
