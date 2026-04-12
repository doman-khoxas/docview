"""Sidebar container with tabbed panels."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor, QIcon
from app.config import SIDEBAR_WIDTH, THUMBNAIL_WIDTH
from app.ui.theme import BG_SURFACE, TEXT_SECONDARY
from app.ui.sidebar.vault_browser import VaultBrowser


class SidebarPanel(QWidget):
    """Left sidebar with Thumbnails, TOC, and Annotations tabs."""

    page_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.South)
        layout.addWidget(self._tabs)

        # Thumbnails tab
        self._thumbnails = QListWidget()
        self._thumbnails.setIconSize(self._thumbnails.size())
        self._thumbnails.setSpacing(4)
        self._thumbnails.itemClicked.connect(self._on_thumbnail_clicked)
        self._tabs.addTab(self._thumbnails, "Pages")

        # TOC tab
        self._toc = QTreeWidget()
        self._toc.setHeaderHidden(True)
        self._toc.itemClicked.connect(self._on_toc_clicked)
        self._tabs.addTab(self._toc, "TOC")

        # Annotations tab
        self._annotations = QListWidget()
        self._tabs.addTab(self._annotations, "Notes")

        # Vault browser tab
        self._vault_browser = VaultBrowser()
        self._vault_browser.file_open_requested.connect(self._on_vault_file_open)
        self._tabs.addTab(self._vault_browser, "Vault")

    def load_thumbnails(self, pdf_doc):
        """Generate thumbnail icons for all pages."""
        self._thumbnails.clear()
        if not pdf_doc or not pdf_doc.is_open:
            return

        import fitz
        for i in range(pdf_doc.page_count):
            page = pdf_doc.doc[i]
            # Render small thumbnail
            zoom = THUMBNAIL_WIDTH / page.rect.width
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            qpix = QPixmap.fromImage(qimg)

            item = QListWidgetItem()
            item.setIcon(QIcon(qpix))
            item.setText(f"Page {i + 1}")
            item.setData(Qt.UserRole, i)
            self._thumbnails.addItem(item)

    def load_toc(self, pdf_doc):
        """Load document table of contents."""
        self._toc.clear()
        if not pdf_doc or not pdf_doc.is_open:
            return

        toc = pdf_doc.doc.get_toc()
        if not toc:
            item = QTreeWidgetItem(["No table of contents"])
            item.setForeground(0, QColor(TEXT_SECONDARY))
            self._toc.addTopLevelItem(item)
            return

        stack: list[QTreeWidgetItem] = []
        for level, title, page in toc:
            item = QTreeWidgetItem([f"{title} (p.{page})"])
            item.setData(0, Qt.UserRole, page - 1)

            while len(stack) >= level:
                stack.pop()

            if stack:
                stack[-1].addChild(item)
            else:
                self._toc.addTopLevelItem(item)
            stack.append(item)

    def _on_thumbnail_clicked(self, item: QListWidgetItem):
        page_num = item.data(Qt.UserRole)
        if page_num is not None:
            self.page_clicked.emit(page_num)

    def _on_toc_clicked(self, item: QTreeWidgetItem, column: int):
        page_num = item.data(0, Qt.UserRole)
        if page_num is not None:
            self.page_clicked.emit(page_num)

    def highlight_page(self, page_num: int):
        """Highlight the active page in thumbnails."""
        self._thumbnails.blockSignals(True)
        if 0 <= page_num < self._thumbnails.count():
            self._thumbnails.setCurrentRow(page_num)
        self._thumbnails.blockSignals(False)

    def set_vault_path(self, path: str):
        """Configure the vault browser root."""
        self._vault_browser.set_vault_path(path)

    def _on_vault_file_open(self, path: str):
        """Proxy vault file open to page_clicked with special handling."""
        self.page_clicked.emit(-1)  # Sentinel: handled by main window
        # Store the path for main window to retrieve
        self._pending_vault_file = path

    @property
    def pending_vault_file(self) -> str | None:
        result = getattr(self, '_pending_vault_file', None)
        self._pending_vault_file = None
        return result
