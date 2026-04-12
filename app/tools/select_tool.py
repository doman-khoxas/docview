"""Select/move existing annotations."""
import math
from PyQt5.QtCore import QPointF
from app.tools.base_tool import BaseTool
from app.core.pdf_renderer import get_render_scale
from app.core.annotation_model import LineAnnotation


class SelectTool(BaseTool):
    def __init__(self, main_window):
        super().__init__(main_window)
        self._selected_annot = None
        self._drag_start = None

    def on_press(self, page_pos: QPointF):
        self._selected_annot = self._find_annotation_at(page_pos)
        if self._selected_annot:
            self._drag_start = page_pos

    def on_drag(self, page_pos: QPointF):
        if not self._selected_annot or not self._drag_start:
            return
        dx = page_pos.x() - self._drag_start.x()
        dy = page_pos.y() - self._drag_start.y()
        self._drag_start = page_pos

        scale = get_render_scale(self.viewport.zoom)
        pdf_dx = dx / scale
        pdf_dy = dy / scale

        annot = self._selected_annot
        if hasattr(annot, 'x0'):
            annot.x0 += pdf_dx
            annot.y0 += pdf_dy
            annot.x1 += pdf_dx
            annot.y1 += pdf_dy
        elif hasattr(annot, 'x'):
            annot.x += pdf_dx
            annot.y += pdf_dy
        elif hasattr(annot, 'points'):
            annot.points = [(px + pdf_dx, py + pdf_dy) for px, py in annot.points]

        self._refresh_page()

    def on_release(self, page_pos: QPointF):
        self._drag_start = None

    def delete_selected(self):
        if self._selected_annot:
            page_num = self.viewport.current_page
            self.pdf_doc.remove_pending_annotation(page_num, self._selected_annot)
            self._selected_annot = None
            self._refresh_page()

    def _find_annotation_at(self, page_pos: QPointF):
        scale = get_render_scale(self.viewport.zoom)
        px, py = page_pos.x() / scale, page_pos.y() / scale
        page_num = self.viewport.current_page
        annotations = self.pdf_doc.get_pending_annotations(page_num)

        for annot in reversed(annotations):
            if hasattr(annot, 'x0') and hasattr(annot, 'x1'):
                ax0, ax1 = min(annot.x0, annot.x1), max(annot.x0, annot.x1)
                ay0, ay1 = min(annot.y0, annot.y1), max(annot.y0, annot.y1)
                if isinstance(annot, LineAnnotation):
                    if self._point_near_line(px, py, annot.x0, annot.y0, annot.x1, annot.y1, 8):
                        return annot
                elif ax0 <= px <= ax1 and ay0 <= py <= ay1:
                    return annot
            elif hasattr(annot, 'x') and hasattr(annot, 'y'):
                if abs(px - annot.x) < 20 and abs(py - annot.y) < 20:
                    return annot
            elif hasattr(annot, 'points') and annot.points:
                for pt_x, pt_y in annot.points:
                    if abs(px - pt_x) < 10 and abs(py - pt_y) < 10:
                        return annot
        return None

    @staticmethod
    def _point_near_line(px, py, x0, y0, x1, y1, tolerance):
        dx, dy = x1 - x0, y1 - y0
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return math.hypot(px - x0, py - y0) <= tolerance
        t = max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / length_sq))
        proj_x, proj_y = x0 + t * dx, y0 + t * dy
        return math.hypot(px - proj_x, py - proj_y) <= tolerance
