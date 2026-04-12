"""Signature placement tool — place saved signature image on PDF page."""
import io
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QPen, QColor, QBrush, QImage
from PyQt5.QtCore import QPointF, QRectF, Qt, QBuffer, QIODevice
from app.tools.base_tool import BaseTool
from app.core.annotation_model import ImageAnnotation


class SignatureTool(BaseTool):
    """Click to place a signature on the page."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self._start = None
        self._sig_data: bytes | None = None
        self._sig_image: QImage | None = None

    def _ensure_signature(self) -> bool:
        """Load or prompt for a signature. Returns True if we have one."""
        if self._sig_data:
            return True

        # Try loading last saved signature
        from app.ui.dialogs.signature_dialog import SignatureDialog
        img = SignatureDialog.get_last_signature()
        if img:
            self._sig_image = img
            self._sig_data = self._qimage_to_bytes(img)
            return True

        # Prompt user to create one
        dlg = SignatureDialog(self.main_window)
        if dlg.exec_():
            img = dlg.signature_image
            if img:
                self._sig_image = img
                self._sig_data = self._qimage_to_bytes(img)
                return True
        return False

    @staticmethod
    def _qimage_to_bytes(img: QImage) -> bytes:
        buf = QBuffer()
        buf.open(QIODevice.WriteOnly)
        img.save(buf, "PNG")
        return bytes(buf.data())

    def on_press(self, page_pos: QPointF):
        if not self._ensure_signature():
            return
        self._start = page_pos

    def on_drag(self, page_pos: QPointF):
        if not self._start or not self._sig_data:
            return
        self._clear_temp()
        s0 = self.page_to_scene(self._start)
        s1 = self.page_to_scene(page_pos)
        rect = QRectF(s0, s1).normalized()
        pen = QPen(QColor("#007acc"), 1.5, Qt.DashLine)
        brush = QBrush(QColor(0, 122, 204, 20))
        item = self.scene.addRect(rect, pen, brush)
        self._temp_items.append(item)

    def on_release(self, page_pos: QPointF):
        if not self._start or not self._sig_data:
            return
        self._clear_temp()

        _, x0, y0 = self.page_to_pdf(QPointF(min(self._start.x(), page_pos.x()),
                                              min(self._start.y(), page_pos.y())))
        _, x1, y1 = self.page_to_pdf(QPointF(max(self._start.x(), page_pos.x()),
                                              max(self._start.y(), page_pos.y())))

        w = abs(x1 - x0)
        h = abs(y1 - y0)
        if w < 10 or h < 10:
            # Default signature size
            w, h = 150, 50

        annot = ImageAnnotation(
            page_num=self.viewport.current_page,
            x=x0, y=y0,
            width=w, height=h,
            image_path="",
            image_data=self._sig_data,
        )
        self._add_annotation(self.viewport.current_page, annot)
        self._refresh_page()
        self._start = None
