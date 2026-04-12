"""Draw circle/ellipse annotations."""
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import QPointF, QRectF, Qt
from app.tools.base_tool import BaseTool
from app.core.annotation_model import CircleAnnotation


class CircleTool(BaseTool):
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
        pen = QPen(QColor(self.stroke_color), self.border_width, Qt.DashLine)
        item = self.scene.addEllipse(rect, pen)
        self._temp_items.append(item)

    def on_release(self, page_pos: QPointF):
        if not self._start:
            return
        self._clear_temp()

        _, x0, y0 = self.page_to_pdf(QPointF(min(self._start.x(), page_pos.x()),
                                              min(self._start.y(), page_pos.y())))
        _, x1, y1 = self.page_to_pdf(QPointF(max(self._start.x(), page_pos.x()),
                                              max(self._start.y(), page_pos.y())))

        annot = CircleAnnotation(
            page_num=self.viewport.current_page,
            color=self.stroke_color,
            opacity=self.opacity,
            x0=x0, y0=y0, x1=x1, y1=y1,
            border_width=self.border_width,
        )
        self._add_annotation(self.viewport.current_page, annot)
        self._refresh_page()
        self._start = None
