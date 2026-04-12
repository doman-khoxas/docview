"""Abstract base class for annotation tools (PyQt5 version)."""
from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItem
from PyQt5.QtCore import QPointF


class BaseTool(ABC):
    def __init__(self, main_window):
        self.main_window = main_window
        self._temp_items: list[QGraphicsItem] = []

    @property
    def viewport(self):
        return self.main_window._pdf_viewport

    @property
    def scene(self) -> QGraphicsScene:
        return self.viewport.scene()

    @property
    def pdf_doc(self):
        return self.main_window.doc_manager.active_document

    def page_to_pdf(self, page_pos: QPointF):
        """Convert page-relative pixel coords to PDF points (page_num, pdf_x, pdf_y).

        page_pos is relative to the rendered page image's top-left corner.
        """
        from app.config import RENDER_DPI
        scale = self.viewport.zoom * RENDER_DPI / 72
        page_num = self.viewport.current_page
        return page_num, page_pos.x() / scale, page_pos.y() / scale

    def page_to_scene(self, page_pos: QPointF) -> QPointF:
        """Convert page-relative pixel coords to scene coords for drawing overlays."""
        page_num = self.viewport.current_page
        items = self.viewport._page_items
        if 0 <= page_num < len(items):
            item = items[page_num]
            rect = item.sceneBoundingRect()
            return QPointF(rect.left() + page_pos.x(), rect.top() + page_pos.y())
        return page_pos

    @property
    def properties(self):
        """Access annotation properties (color, opacity, etc.)."""
        return self.main_window._properties_panel if hasattr(self.main_window, '_properties_panel') else None

    @property
    def stroke_color(self) -> str:
        if self.properties and hasattr(self.properties, 'stroke_color'):
            return self.properties.stroke_color
        from app.config import DEFAULT_ANNOT_COLOR
        return DEFAULT_ANNOT_COLOR

    @property
    def highlight_color(self) -> str:
        if self.properties and hasattr(self.properties, 'highlight_color'):
            return self.properties.highlight_color
        from app.config import DEFAULT_HIGHLIGHT_COLOR
        return DEFAULT_HIGHLIGHT_COLOR

    @property
    def opacity(self) -> float:
        if self.properties and hasattr(self.properties, 'opacity'):
            return self.properties.opacity
        from app.config import DEFAULT_OPACITY
        return DEFAULT_OPACITY

    @property
    def border_width(self) -> float:
        if self.properties and hasattr(self.properties, 'border_width'):
            return self.properties.border_width
        from app.config import DEFAULT_BORDER_WIDTH
        return DEFAULT_BORDER_WIDTH

    @property
    def font_size(self) -> float:
        if self.properties and hasattr(self.properties, 'font_size'):
            return self.properties.font_size
        from app.config import DEFAULT_FONT_SIZE
        return DEFAULT_FONT_SIZE

    @abstractmethod
    def on_press(self, scene_pos: QPointF):
        pass

    @abstractmethod
    def on_drag(self, scene_pos: QPointF):
        pass

    @abstractmethod
    def on_release(self, scene_pos: QPointF):
        pass

    def _clear_temp(self):
        for item in self._temp_items:
            if item.scene():
                item.scene().removeItem(item)
        self._temp_items.clear()

    def _add_annotation(self, page_num: int, annotation):
        """Add annotation via command stack for undo/redo support."""
        from app.core.command import AddAnnotationCommand
        stack = self.main_window.command_stack
        if stack:
            cmd = AddAnnotationCommand(self.pdf_doc, page_num, annotation)
            stack.push(cmd)
            self.main_window._update_undo_redo_state()
        else:
            self.pdf_doc.add_pending_annotation(page_num, annotation)

    def _refresh_page(self):
        """Re-render the current page after annotation change."""
        page_items = self.viewport._page_items
        current = self.viewport.current_page
        if 0 <= current < len(page_items):
            page_items[current].invalidate()
            doc = self.pdf_doc
            if doc and doc.is_open:
                page_items[current].render(doc.doc, self.viewport.zoom)
