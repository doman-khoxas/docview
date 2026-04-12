"""QGraphicsPixmapItem for a single PDF page with lazy rendering."""
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsDropShadowEffect
from PyQt5.QtGui import QPixmap, QImage, QColor, QPen, QBrush
from PyQt5.QtCore import Qt, QRectF
import fitz
from app.config import RENDER_DPI, PAGE_SHADOW_OFFSET


class PDFPageItem(QGraphicsPixmapItem):
    """Represents a single rendered PDF page in the graphics scene."""

    def __init__(self, page_num: int, page_rect: fitz.Rect, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.page_rect = page_rect
        self._rendered = False
        self._render_zoom = 0.0

        # White placeholder at correct aspect ratio
        w = int(page_rect.width * RENDER_DPI / 72)
        h = int(page_rect.height * RENDER_DPI / 72)
        placeholder = QPixmap(max(w, 1), max(h, 1))
        placeholder.fill(QColor("#ffffff"))
        self.setPixmap(placeholder)

    @property
    def rendered(self) -> bool:
        return self._rendered

    def render(self, fitz_doc: fitz.Document, zoom: float = 1.0):
        """Render this page from the PDF document at the given zoom level."""
        if self._rendered and abs(self._render_zoom - zoom) < 0.001:
            return

        page = fitz_doc[self.page_num]
        scale = zoom * RENDER_DPI / 72
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        qpix = QPixmap.fromImage(qimg)
        self.setPixmap(qpix)
        self._rendered = True
        self._render_zoom = zoom

    def invalidate(self):
        """Mark as needing re-render (e.g., after zoom change)."""
        self._rendered = False
        self._render_zoom = 0.0
