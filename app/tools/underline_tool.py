"""Drag-to-underline tool with text-snapping."""
import fitz
from app.tools.base_tool import BaseTool
from app.core.annotation_model import UnderlineAnnotation
from app.core.pdf_renderer import canvas_to_pdf_coords


class UnderlineTool(BaseTool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self._start = None

    def on_press(self, x: float, y: float):
        self._start = (x, y)

    def on_drag(self, x: float, y: float):
        if not self._start:
            return
        self._clear_temp()
        item = self.canvas.create_rectangle(
            self._start[0], self._start[1], x, y,
            fill="", outline=self.properties.stroke_color,
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

        doc = self.app_ref.pdf_doc
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

        annot = UnderlineAnnotation(
            page_num=self.viewport.current_page,
            color=self.properties.stroke_color,
            opacity=self.properties.opacity,
            quads=quads,
        )
        page_num = self.viewport.current_page
        doc.add_pending_annotation(page_num, annot)
        self.app_ref.push_undo(page_num, annot)
        self.viewport.render_current_page()
        self._start = None
