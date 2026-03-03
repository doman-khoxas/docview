"""Click-to-place image annotation tool — opens file dialog, then drag to size."""
from tkinter import filedialog
from app.tools.base_tool import BaseTool
from app.core.annotation_model import ImageAnnotation
from app.core.pdf_renderer import canvas_to_pdf_coords


class ImageTool(BaseTool):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self._image_path: str | None = None
        self._start = None

    def on_press(self, x: float, y: float):
        if not self._image_path:
            path = filedialog.askopenfilename(
                filetypes=[
                    ("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                    ("All files", "*.*"),
                ]
            )
            if not path:
                return
            self._image_path = path
        self._start = (x, y)

    def on_drag(self, x: float, y: float):
        if not self._start or not self._image_path:
            return
        self._clear_temp()
        item = self.canvas.create_rectangle(
            self._start[0], self._start[1], x, y,
            outline="#4A9EFF", width=2, dash=(6, 3), tags="temp_annotation"
        )
        self._temp_items.append(item)
        # Label showing it's an image placement
        label = self.canvas.create_text(
            (self._start[0] + x) / 2, (self._start[1] + y) / 2,
            text="[IMG]", fill="#4A9EFF",
            font=("Segoe UI", 10), tags="temp_annotation"
        )
        self._temp_items.append(label)

    def on_release(self, x: float, y: float):
        if not self._start or not self._image_path:
            return
        self._clear_temp()

        # Ignore tiny accidental clicks
        if abs(x - self._start[0]) < 10 or abs(y - self._start[1]) < 10:
            self._start = None
            return

        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            self._start = None
            return

        zoom = self.viewport.zoom
        x0, y0 = canvas_to_pdf_coords(
            min(self._start[0], x), min(self._start[1], y), zoom)
        x1, y1 = canvas_to_pdf_coords(
            max(self._start[0], x), max(self._start[1], y), zoom)

        annot = ImageAnnotation(
            page_num=self.viewport.current_page,
            x0=x0, y0=y0, x1=x1, y1=y1,
            image_path=self._image_path,
        )
        page_num = self.viewport.current_page
        doc.add_pending_annotation(page_num, annot)
        self.app_ref.push_undo(page_num, annot)
        self.viewport.render_current_page()

        self._start = None
        self._image_path = None  # reset for next use
