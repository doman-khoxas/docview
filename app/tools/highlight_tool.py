"""Drag-to-highlight tool with text-snapping."""
import fitz
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtCore import QPointF, QRectF, Qt
from app.tools.base_tool import BaseTool
from app.core.annotation_model import HighlightAnnotation


class HighlightTool(BaseTool):
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
        brush = QBrush(QColor(255, 255, 0, 80))
        item = self.scene.addRect(rect, QPen(Qt.NoPen), brush)
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

        sel_rect = fitz.Rect(x0, y0, x1, y1)
        words = page.get_text("words")
        quads = []
        for w in words:
            word_rect = fitz.Rect(w[:4])
            if sel_rect.intersects(word_rect):
                quads.append(word_rect.quad)

        if not quads:
            quads = [sel_rect.quad]

        annot = HighlightAnnotation(
            page_num=self.viewport.current_page,
            color=self.highlight_color,
            opacity=self.opacity,
            quads=quads,
        )
        self._add_annotation(self.viewport.current_page, annot)
        self._refresh_page()
        self._start = None
