"""Click-to-place freetext annotation tool."""
from app.tools.base_tool import BaseTool
from app.core.annotation_model import FreetextAnnotation
from app.core.pdf_renderer import canvas_to_pdf_coords


class TextTool(BaseTool):
    def __init__(self, app_ref):
        super().__init__(app_ref)

    def on_press(self, x: float, y: float):
        pass

    def on_drag(self, x: float, y: float):
        pass

    def on_release(self, x: float, y: float):
        from app.ui.dialogs.text_input_dialog import TextInputDialog

        zoom = self.viewport.zoom
        px, py = canvas_to_pdf_coords(x, y, zoom)

        dialog = TextInputDialog(self.app_ref)
        self.app_ref.wait_window(dialog)

        text = dialog.result
        if text:
            annot = FreetextAnnotation(
                page_num=self.viewport.current_page,
                x=px, y=py,
                text=text,
                font_size=self.properties.font_size,
                text_color=self.properties.stroke_color,
                opacity=self.properties.opacity,
            )
            page_num = self.viewport.current_page
            self.app_ref.pdf_doc.add_pending_annotation(page_num, annot)
            self.app_ref.push_undo(page_num, annot)
            self.viewport.render_current_page()
