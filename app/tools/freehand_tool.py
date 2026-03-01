"""Ink/freehand drawing tool with point decimation."""
from app.tools.base_tool import BaseTool
from app.core.annotation_model import InkAnnotation
from app.core.pdf_renderer import canvas_to_pdf_coords
import math


class FreehandTool(BaseTool):
    MIN_DISTANCE = 3  # minimum pixel distance between recorded points

    def __init__(self, app_ref):
        super().__init__(app_ref)
        self._points = []
        self._canvas_points = []

    def on_press(self, x: float, y: float):
        self._points.clear()
        self._canvas_points.clear()
        self._canvas_points.append((x, y))

        zoom = self.viewport.zoom
        px, py = canvas_to_pdf_coords(x, y, zoom)
        self._points.append((px, py))

    def on_drag(self, x: float, y: float):
        if not self._canvas_points:
            return

        last_x, last_y = self._canvas_points[-1]
        dist = math.hypot(x - last_x, y - last_y)
        if dist < self.MIN_DISTANCE:
            return

        self._canvas_points.append((x, y))
        zoom = self.viewport.zoom
        px, py = canvas_to_pdf_coords(x, y, zoom)
        self._points.append((px, py))

        if len(self._canvas_points) >= 2:
            self._clear_temp()
            coords = []
            for cx, cy in self._canvas_points:
                coords.extend([cx, cy])
            item = self.canvas.create_line(
                *coords, fill=self.properties.stroke_color,
                width=self.properties.border_width,
                smooth=True, tags="temp_annotation"
            )
            self._temp_items.append(item)

    def on_release(self, x: float, y: float):
        self._clear_temp()
        if len(self._points) < 2:
            return

        annot = InkAnnotation(
            page_num=self.viewport.current_page,
            color=self.properties.stroke_color,
            opacity=self.properties.opacity,
            points=list(self._points),
            border_width=self.properties.border_width,
        )
        self.app_ref.pdf_doc.add_pending_annotation(self.viewport.current_page, annot)
        self.viewport.render_current_page()
        self._points.clear()
        self._canvas_points.clear()
