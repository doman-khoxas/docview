"""Ink/freehand drawing tool with point decimation."""
import math
from PyQt5.QtGui import QPen, QColor, QPainterPath
from PyQt5.QtCore import QPointF
from app.tools.base_tool import BaseTool
from app.core.annotation_model import InkAnnotation


class FreehandTool(BaseTool):
    MIN_DISTANCE = 3

    def __init__(self, main_window):
        super().__init__(main_window)
        self._pdf_points = []
        self._page_points = []
        self._path_item = None

    def on_press(self, page_pos: QPointF):
        self._pdf_points.clear()
        self._page_points.clear()
        self._page_points.append(page_pos)

        _, px, py = self.page_to_pdf(page_pos)
        self._pdf_points.append((px, py))

        scene_pos = self.page_to_scene(page_pos)
        path = QPainterPath(scene_pos)
        pen = QPen(QColor(self.stroke_color), self.border_width)
        pen.setCapStyle(1)   # RoundCap
        pen.setJoinStyle(0x80)  # RoundJoin
        self._path_item = self.scene.addPath(path, pen)
        self._temp_items.append(self._path_item)

    def on_drag(self, page_pos: QPointF):
        if not self._page_points:
            return

        last = self._page_points[-1]
        dist = math.hypot(page_pos.x() - last.x(), page_pos.y() - last.y())
        if dist < self.MIN_DISTANCE:
            return

        self._page_points.append(page_pos)
        _, px, py = self.page_to_pdf(page_pos)
        self._pdf_points.append((px, py))

        if self._path_item:
            path = self._path_item.path()
            path.lineTo(self.page_to_scene(page_pos))
            self._path_item.setPath(path)

    def on_release(self, page_pos: QPointF):
        self._clear_temp()
        self._path_item = None

        if len(self._pdf_points) < 2:
            return

        annot = InkAnnotation(
            page_num=self.viewport.current_page,
            color=self.stroke_color,
            opacity=self.opacity,
            points=list(self._pdf_points),
            border_width=self.border_width,
        )
        self._add_annotation(self.viewport.current_page, annot)
        self._refresh_page()
        self._pdf_points.clear()
        self._page_points.clear()
