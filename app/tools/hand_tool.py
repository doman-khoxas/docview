"""Hand/pan tool — handled by QGraphicsView.ScrollHandDrag mode."""
from PyQt5.QtCore import QPointF
from app.tools.base_tool import BaseTool


class HandTool(BaseTool):
    """Hand tool for panning. In PyQt5, panning is handled by
    QGraphicsView.ScrollHandDrag mode, so this tool is mostly a no-op."""

    def on_press(self, scene_pos: QPointF):
        pass

    def on_drag(self, scene_pos: QPointF):
        pass

    def on_release(self, scene_pos: QPointF):
        pass
