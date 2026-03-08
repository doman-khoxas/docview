"""Sticky note (popup comment) tool — click to place a note icon."""
from app.tools.base_tool import BaseTool
from app.core.annotation_model import StickyNoteAnnotation
from app.core.pdf_renderer import canvas_to_pdf_coords


class StickyNoteTool(BaseTool):
    def __init__(self, app_ref):
        super().__init__(app_ref)

    def on_press(self, x: float, y: float):
        pass

    def on_drag(self, x: float, y: float):
        pass

    def on_release(self, x: float, y: float):
        zoom = self.viewport.zoom
        pdf_x, pdf_y = canvas_to_pdf_coords(x, y, zoom)

        from app.ui.dialogs.text_input_dialog import TextInputDialog
        dlg = TextInputDialog(self.app_ref, title="Sticky Note", prompt="Enter note text:")
        self.app_ref.wait_window(dlg)
        text = getattr(dlg, "result", None)
        if not text:
            return

        annot = StickyNoteAnnotation(
            page_num=self.viewport.current_page,
            x=pdf_x, y=pdf_y,
            text=text,
            color=self.properties.stroke_color,
            opacity=self.properties.opacity,
        )
        page_num = self.viewport.current_page
        self.app_ref.pdf_doc.add_pending_annotation(page_num, annot)
        self.app_ref.push_undo(page_num, annot)
        self.viewport.render_current_page()
