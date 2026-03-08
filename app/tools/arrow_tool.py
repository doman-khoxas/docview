"""Draw arrow annotations (line with arrowhead)."""
import math
from app.tools.base_tool import BaseTool
from app.core.annotation_model import ArrowAnnotation
from app.core.pdf_renderer import canvas_to_pdf_coords


class ArrowTool(BaseTool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self._start = None

    def on_press(self, x: float, y: float):
        self._start = (x, y)

    def on_drag(self, x: float, y: float):
        if not self._start:
            return
        self._clear_temp()
        sx, sy = self._start
        # Draw line
        item = self.canvas.create_line(
            sx, sy, x, y,
            fill=self.properties.stroke_color,
            width=self.properties.border_width,
            dash=(4, 4), tags="temp_annotation"
        )
        self._temp_items.append(item)
        # Draw arrowhead
        self._draw_arrowhead(sx, sy, x, y, preview=True)

    def on_release(self, x: float, y: float):
        if not self._start:
            return
        self._clear_temp()

        zoom = self.viewport.zoom
        x0, y0 = canvas_to_pdf_coords(self._start[0], self._start[1], zoom)
        x1, y1 = canvas_to_pdf_coords(x, y, zoom)

        annot = ArrowAnnotation(
            page_num=self.viewport.current_page,
            color=self.properties.stroke_color,
            opacity=self.properties.opacity,
            x0=x0, y0=y0, x1=x1, y1=y1,
            border_width=self.properties.border_width,
        )
        page_num = self.viewport.current_page
        self.app_ref.pdf_doc.add_pending_annotation(page_num, annot)
        self.app_ref.push_undo(page_num, annot)
        self.viewport.render_current_page()
        self._start = None

    def _draw_arrowhead(self, x0, y0, x1, y1, preview=False):
        """Draw a triangular arrowhead at (x1, y1)."""
        dx = x1 - x0
        dy = y1 - y0
        length = math.hypot(dx, dy)
        if length < 1:
            return

        # Normalize
        ux, uy = dx / length, dy / length
        # Perpendicular
        px, py = -uy, ux

        head_len = max(10, self.properties.border_width * 5)
        head_w = head_len * 0.4

        # Three points of arrowhead triangle
        tip_x, tip_y = x1, y1
        left_x = x1 - ux * head_len + px * head_w
        left_y = y1 - uy * head_len + py * head_w
        right_x = x1 - ux * head_len - px * head_w
        right_y = y1 - uy * head_len - py * head_w

        tag = "temp_annotation" if preview else "arrow_head"
        item = self.canvas.create_polygon(
            tip_x, tip_y, left_x, left_y, right_x, right_y,
            fill=self.properties.stroke_color, outline=self.properties.stroke_color,
            tags=tag
        )
        self._temp_items.append(item)
