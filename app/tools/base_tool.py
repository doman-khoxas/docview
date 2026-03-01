"""Abstract base class for annotation tools."""
from abc import ABC, abstractmethod


class BaseTool(ABC):
    def __init__(self, app_ref):
        self.app_ref = app_ref
        self._temp_items = []  # canvas item IDs for cleanup

    @property
    def viewport(self):
        return self.app_ref.main_window.viewport

    @property
    def canvas(self):
        """Returns the page canvas proxy so tool drawings are offset-adjusted
        for the continuous viewport.  Falls back to raw canvas."""
        vp = self.viewport
        if hasattr(vp, 'page_canvas_proxy'):
            return vp.page_canvas_proxy
        return vp.canvas

    def canvas_to_pdf(self, cx: float, cy: float):
        """Convert page-relative canvas coords to (page_num, pdf_x, pdf_y)."""
        vp = self.viewport
        if hasattr(vp, 'canvas_to_page_coords'):
            return vp.canvas_to_page_coords(cx, cy)
        from app.core.pdf_renderer import canvas_to_pdf_coords
        px, py = canvas_to_pdf_coords(cx, cy, vp.zoom)
        return vp.current_page, px, py

    @property
    def properties(self):
        return self.app_ref.main_window.properties_panel

    @abstractmethod
    def on_press(self, x: float, y: float):
        pass

    @abstractmethod
    def on_drag(self, x: float, y: float):
        pass

    @abstractmethod
    def on_release(self, x: float, y: float):
        pass

    def _clear_temp(self):
        for item in self._temp_items:
            self.canvas.delete(item)
        self._temp_items.clear()
