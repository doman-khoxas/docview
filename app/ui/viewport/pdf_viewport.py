"""QGraphicsView-based PDF viewport with lazy page rendering, zoom, and tool interaction."""
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen, QWheelEvent, QMouseEvent, QCursor
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QTimer
from app.config import PAGE_GAP, OVERSCAN_PX, ZOOM_MIN, ZOOM_MAX, ZOOM_STEP, ZOOM_DEFAULT, RENDER_DPI
from app.ui.viewport.pdf_page_item import PDFPageItem
from app.ui.theme import CANVAS_BG, PAGE_SHADOW


class PDFViewport(QGraphicsView):
    """Scrollable, zoomable PDF viewport with tool interaction."""

    page_changed = pyqtSignal(int)
    zoom_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._doc = None
        self._page_items: list[PDFPageItem] = []
        self._zoom = ZOOM_DEFAULT
        self._current_page = 0
        self._tool_owner = None  # MainWindow reference for tool access
        self._drawing = False    # True while tool is handling a press-drag-release

        # Rendering
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setBackgroundBrush(QBrush(QColor(CANVAS_BG)))
        self.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)

        # Accept drops
        self.setAcceptDrops(True)

        # Lazy render timer
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(50)
        self._render_timer.timeout.connect(self._render_visible_pages)

        # Connect scroll changes
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def set_tool_owner(self, owner):
        """Set the MainWindow reference for active_tool access."""
        self._tool_owner = owner

    @property
    def _active_tool(self):
        if self._tool_owner and hasattr(self._tool_owner, 'active_tool'):
            return self._tool_owner.active_tool
        return None

    # ── Coordinate conversion ──

    def scene_to_page_coords(self, scene_pos: QPointF) -> tuple[int, QPointF]:
        """Convert scene coordinates to (page_number, page-relative QPointF).

        Returns the page whose bounding rect contains the point, and
        the position relative to that page's top-left corner.
        """
        for item in self._page_items:
            rect = item.sceneBoundingRect()
            if rect.contains(scene_pos):
                local = scene_pos - rect.topLeft()
                return item.page_num, local

        # Fallback: find nearest page
        best = 0
        best_dist = float('inf')
        for item in self._page_items:
            rect = item.sceneBoundingRect()
            cy = rect.center().y()
            dist = abs(scene_pos.y() - cy)
            if dist < best_dist:
                best_dist = dist
                best = item.page_num

        item = self._page_items[best]
        rect = item.sceneBoundingRect()
        # Clamp to page bounds
        local_x = max(0, min(scene_pos.x() - rect.left(), rect.width()))
        local_y = max(0, min(scene_pos.y() - rect.top(), rect.height()))
        return best, QPointF(local_x, local_y)

    # ── Mouse event routing to tools ──

    def mousePressEvent(self, event: QMouseEvent):
        tool = self._active_tool
        if tool and self.dragMode() == QGraphicsView.NoDrag and event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            page_num, page_pos = self.scene_to_page_coords(scene_pos)
            self._current_page = page_num
            self._drawing = True
            tool.on_press(page_pos)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        tool = self._active_tool
        if tool and self._drawing:
            scene_pos = self.mapToScene(event.pos())
            _, page_pos = self.scene_to_page_coords(scene_pos)
            tool.on_drag(page_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        tool = self._active_tool
        if tool and self._drawing and event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            _, page_pos = self.scene_to_page_coords(scene_pos)
            tool.on_release(page_pos)
            self._drawing = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ── Drag-and-drop ──

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls() and self._tool_owner:
            from app.config import ALL_SUPPORTED_EXTENSIONS
            from pathlib import Path
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path and Path(path).suffix.lower() in ALL_SUPPORTED_EXTENSIONS:
                    self._tool_owner.open_file(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    # ── Properties ──

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value: float):
        value = max(ZOOM_MIN, min(ZOOM_MAX, value))
        if abs(value - self._zoom) < 0.001:
            return
        self._zoom = value
        self._relayout_pages()
        self.zoom_changed.emit(self._zoom)

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def page_count(self) -> int:
        return len(self._page_items)

    # ── Document loading ──

    def load_document(self, pdf_doc):
        """Load a PDFDocument and build the page layout."""
        self._scene.clear()
        self._page_items.clear()
        self._doc = pdf_doc
        self._current_page = 0

        if not pdf_doc or not pdf_doc.is_open:
            return

        fitz_doc = pdf_doc.doc

        for i in range(fitz_doc.page_count):
            page = fitz_doc[i]
            item = PDFPageItem(i, page.rect)
            self._scene.addItem(item)
            self._page_items.append(item)

        self._relayout_pages()
        self._render_visible_pages()

    def _relayout_pages(self):
        """Recalculate page positions after zoom change."""
        if not self._page_items or not self._doc:
            return

        scale = self._zoom * RENDER_DPI / 72
        y_offset = PAGE_GAP

        for item in self._page_items:
            item.invalidate()
            w = item.page_rect.width * scale
            h = item.page_rect.height * scale
            item.setPos(-w / 2, y_offset)
            y_offset += h + PAGE_GAP

        total_height = y_offset
        max_width = max(
            item.page_rect.width * scale for item in self._page_items
        ) if self._page_items else 800

        self._scene.setSceneRect(
            -max_width / 2 - 50, 0,
            max_width + 100, total_height
        )

        self._schedule_render()

    def _schedule_render(self):
        self._render_timer.start()

    def _render_visible_pages(self):
        """Render only pages currently visible in the viewport."""
        if not self._doc or not self._doc.is_open or not self._page_items:
            return

        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        expanded = visible_rect.adjusted(0, -OVERSCAN_PX, 0, OVERSCAN_PX)

        fitz_doc = self._doc.doc
        for item in self._page_items:
            item_rect = item.sceneBoundingRect()
            if item_rect.intersects(expanded):
                if not item.rendered:
                    item.render(fitz_doc, self._zoom)

        self._update_current_page(visible_rect)

    def _update_current_page(self, visible_rect: QRectF):
        best_page = 0
        best_overlap = 0.0

        for item in self._page_items:
            item_rect = item.sceneBoundingRect()
            intersection = item_rect.intersected(visible_rect)
            area = intersection.width() * intersection.height()
            if area > best_overlap:
                best_overlap = area
                best_page = item.page_num

        if best_page != self._current_page:
            self._current_page = best_page
            self.page_changed.emit(self._current_page)

    def _on_scroll(self):
        self._schedule_render()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._schedule_render()

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    # ── Navigation ──

    def zoom_in(self):
        self.zoom = self._zoom + ZOOM_STEP

    def zoom_out(self):
        self.zoom = self._zoom - ZOOM_STEP

    def zoom_fit_width(self):
        if not self._page_items:
            return
        page_width = self._page_items[0].page_rect.width
        viewport_width = self.viewport().width() - 40
        self.zoom = viewport_width / (page_width * RENDER_DPI / 72)

    def go_to_page(self, page_num: int):
        if 0 <= page_num < len(self._page_items):
            item = self._page_items[page_num]
            self.centerOn(item)
            self._current_page = page_num
            self.page_changed.emit(page_num)
            self._schedule_render()

    def get_scroll_y(self) -> float:
        return self.verticalScrollBar().value()

    def set_scroll_y(self, y: float):
        self.verticalScrollBar().setValue(int(y))

    def next_page(self):
        if self._current_page < len(self._page_items) - 1:
            self.go_to_page(self._current_page + 1)

    def prev_page(self):
        if self._current_page > 0:
            self.go_to_page(self._current_page - 1)
