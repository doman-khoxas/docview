"""Click-to-place freetext annotation tool."""
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtCore import QPointF
from app.tools.base_tool import BaseTool
from app.core.annotation_model import FreetextAnnotation


class TextTool(BaseTool):
    def __init__(self, main_window):
        super().__init__(main_window)

    def on_press(self, page_pos: QPointF):
        pass

    def on_drag(self, page_pos: QPointF):
        pass

    def on_release(self, page_pos: QPointF):
        _, px, py = self.page_to_pdf(page_pos)

        text, ok = QInputDialog.getMultiLineText(
            self.main_window, "Add Text", "Enter text:")
        if ok and text:
            annot = FreetextAnnotation(
                page_num=self.viewport.current_page,
                x=px, y=py,
                text=text,
                font_size=self.font_size,
                text_color=self.stroke_color,
                opacity=self.opacity,
            )
            self._add_annotation(self.viewport.current_page, annot)
            self._refresh_page()
