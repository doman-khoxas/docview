"""Draw redaction rectangles — areas marked for permanent removal."""
from app.tools.base_tool import BaseTool
from app.core.annotation_model import RedactAnnotation
from app.core.pdf_renderer import canvas_to_pdf_coords


class RedactTool(BaseTool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self._start = None

    def on_press(self, x: float, y: float):
        self._start = (x, y)

    def on_drag(self, x: float, y: float):
        if not self._start:
            return
        self._clear_temp()
        # Draw a red-outlined dashed rectangle as preview
        item = self.canvas.create_rectangle(
            self._start[0], self._start[1], x, y,
            outline="#ED4245",
            width=2,
            dash=(6, 3),
            tags="temp_annotation"
        )
        self._temp_items.append(item)
        # Semi-transparent fill preview
        fill_item = self.canvas.create_rectangle(
            self._start[0], self._start[1], x, y,
            fill="#ED4245",
            outline="",
            stipple="gray25",
            tags="temp_annotation"
        )
        self._temp_items.append(fill_item)

    def on_release(self, x: float, y: float):
        if not self._start:
            return
        self._clear_temp()

        # Ignore tiny accidental clicks
        if abs(x - self._start[0]) < 5 or abs(y - self._start[1]) < 5:
            self._start = None
            return

        zoom = self.viewport.zoom
        x0, y0 = canvas_to_pdf_coords(
            min(self._start[0], x), min(self._start[1], y), zoom)
        x1, y1 = canvas_to_pdf_coords(
            max(self._start[0], x), max(self._start[1], y), zoom)

        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            self._start = None
            return

        annot = RedactAnnotation(
            page_num=self.viewport.current_page,
            x0=x0, y0=y0, x1=x1, y1=y1,
        )
        page_num = self.viewport.current_page
        doc.add_pending_annotation(page_num, annot)
        self.app_ref.push_undo(page_num, annot)
        self.viewport.render_current_page()
        self._start = None
