"""Image insertion tool — pick an image file, then drag to place on page."""
from pathlib import Path
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QPen, QColor, QBrush, QPixmap
from PyQt5.QtCore import QPointF, QRectF, Qt
from app.tools.base_tool import BaseTool
from app.core.annotation_model import ImageAnnotation


IMAGE_FILTERS = "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.svg);;All Files (*.*)"


class ImageTool(BaseTool):
    """Click to pick an image, then drag to place and size it on the page."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self._start = None
        self._image_path: str | None = None
        self._image_data: bytes | None = None

    def on_press(self, page_pos: QPointF):
        # If no image selected yet, prompt for one
        if not self._image_data:
            path, _ = QFileDialog.getOpenFileName(
                self.main_window, "Select Image", "", IMAGE_FILTERS)
            if not path:
                return
            self._image_path = path
            self._image_data = Path(path).read_bytes()

        self._start = page_pos

    def on_drag(self, page_pos: QPointF):
        if not self._start or not self._image_data:
            return
        self._clear_temp()
        s0 = self.page_to_scene(self._start)
        s1 = self.page_to_scene(page_pos)
        rect = QRectF(s0, s1).normalized()
        # Preview rectangle with image indication
        pen = QPen(QColor("#007acc"), 2, Qt.DashLine)
        brush = QBrush(QColor(0, 122, 204, 30))
        item = self.scene.addRect(rect, pen, brush)
        self._temp_items.append(item)

    def on_release(self, page_pos: QPointF):
        if not self._start or not self._image_data:
            return
        self._clear_temp()

        _, x0, y0 = self.page_to_pdf(QPointF(min(self._start.x(), page_pos.x()),
                                              min(self._start.y(), page_pos.y())))
        _, x1, y1 = self.page_to_pdf(QPointF(max(self._start.x(), page_pos.x()),
                                              max(self._start.y(), page_pos.y())))

        w = abs(x1 - x0)
        h = abs(y1 - y0)
        if w < 5 or h < 5:
            # Too small — use default size
            w, h = 150, 150

        annot = ImageAnnotation(
            page_num=self.viewport.current_page,
            x=x0, y=y0,
            width=w, height=h,
            image_path=self._image_path or "",
            image_data=self._image_data,
        )
        self._add_annotation(self.viewport.current_page, annot)
        self._refresh_page()

        # Reset for next image
        self._start = None
        self._image_path = None
        self._image_data = None
