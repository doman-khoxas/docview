"""Draw circle/ellipse annotations."""
from app.tools.base_tool import BaseTool
from app.core.annotation_model import CircleAnnotation
from app.core.pdf_renderer import canvas_to_pdf_coords


class CircleTool(BaseTool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self._start = None

    def on_press(self, x: float, y: float):
        self._start = (x, y)

    def on_drag(self, x: float, y: float):
        if not self._start:
            return
        self._clear_temp()
        item = self.canvas.create_oval(
            self._start[0], self._start[1], x, y,
            outline=self.properties.stroke_color,
            width=self.properties.border_width,
            dash=(4, 4), tags="temp_annotation"
        )
        self._temp_items.append(item)

    def on_release(self, x: float, y: float):
        if not self._start:
            return
        self._clear_temp()

        zoom = self.viewport.zoom
        x0, y0 = canvas_to_pdf_coords(min(self._start[0], x), min(self._start[1], y), zoom)
        x1, y1 = canvas_to_pdf_coords(max(self._start[0], x), max(self._start[1], y), zoom)

        annot = CircleAnnotation(
            page_num=self.viewport.current_page,
            color=self.properties.stroke_color,
            opacity=self.properties.opacity,
            x0=x0, y0=y0, x1=x1, y1=y1,
            border_width=self.properties.border_width,
        )
        self.app_ref.pdf_doc.add_pending_annotation(self.viewport.current_page, annot)
        self.viewport.render_current_page()
        self._start = None
