"""Redaction tool -- draw areas to black-out permanently."""
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtCore import QPointF, QRectF, Qt
from app.tools.base_tool import BaseTool


class RedactTool(BaseTool):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._start = None

    def on_press(self, page_pos: QPointF):
        self._start = page_pos

    def on_drag(self, page_pos: QPointF):
        if not self._start:
            return
        self._clear_temp()
        s0 = self.page_to_scene(self._start)
        s1 = self.page_to_scene(page_pos)
        rect = QRectF(s0, s1).normalized()
        pen = QPen(QColor("#ff0000"), 2, Qt.DashLine)
        brush = QBrush(QColor(255, 0, 0, 40))
        item = self.scene.addRect(rect, pen, brush)
        self._temp_items.append(item)

    def on_release(self, page_pos: QPointF):
        if not self._start:
            return
        self._clear_temp()

        _, x0, y0 = self.page_to_pdf(QPointF(min(self._start.x(), page_pos.x()),
                                              min(self._start.y(), page_pos.y())))
        _, x1, y1 = self.page_to_pdf(QPointF(max(self._start.x(), page_pos.x()),
                                              max(self._start.y(), page_pos.y())))

        doc = self.pdf_doc
        page = doc.get_page(self.viewport.current_page)
        import fitz
        rect = fitz.Rect(x0, y0, x1, y1)
        page.add_redact_annot(rect, fill=(0, 0, 0))
        page.apply_redactions()
        doc.modified = True

        self._refresh_page()
        self._start = None
