"""Stamp annotation tool — drag to place a stamp rectangle."""
from app.tools.base_tool import BaseTool
from app.core.annotation_model import StampAnnotation
from app.core.pdf_renderer import canvas_to_pdf_coords

# Available stamp types
STAMP_TYPES = [
    "APPROVED", "CONFIDENTIAL", "DRAFT", "FINAL",
    "NOT APPROVED", "VOID", "FOR REVIEW",
]


class StampTool(BaseTool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self._start = None
        self.stamp_text = "APPROVED"

    def on_press(self, x: float, y: float):
        self._start = (x, y)

    def on_drag(self, x: float, y: float):
        if not self._start:
            return
        self._clear_temp()
        sx, sy = self._start
        # Draw preview rectangle with stamp text
        item = self.canvas.create_rectangle(
            sx, sy, x, y,
            outline=self.properties.stroke_color,
            dash=(6, 3), width=2, tags="temp_annotation"
        )
        self._temp_items.append(item)
        # Draw stamp text in center
        cx_mid = (sx + x) / 2
        cy_mid = (sy + y) / 2
        txt = self.canvas.create_text(
            cx_mid, cy_mid, text=self.stamp_text,
            fill=self.properties.stroke_color,
            font=("Segoe UI", 14, "bold"),
            tags="temp_annotation"
        )
        self._temp_items.append(txt)

    def on_release(self, x: float, y: float):
        if not self._start:
            return
        self._clear_temp()

        zoom = self.viewport.zoom
        x0, y0 = canvas_to_pdf_coords(
            min(self._start[0], x), min(self._start[1], y), zoom)
        x1, y1 = canvas_to_pdf_coords(
            max(self._start[0], x), max(self._start[1], y), zoom)

        # Minimum size check
        if abs(x1 - x0) < 20 or abs(y1 - y0) < 10:
            # Auto-size if drag area too small
            x1 = x0 + 120
            y1 = y0 + 40

        annot = StampAnnotation(
            page_num=self.viewport.current_page,
            x0=x0, y0=y0, x1=x1, y1=y1,
            stamp_text=self.stamp_text,
            color=self.properties.stroke_color,
            opacity=self.properties.opacity,
        )
        page_num = self.viewport.current_page
        self.app_ref.pdf_doc.add_pending_annotation(page_num, annot)
        self.app_ref.push_undo(page_num, annot)
        self.viewport.render_current_page()
        self._start = None
