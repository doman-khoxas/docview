"""Default pan tool — click-drag scrolls the viewport via canvas scan."""
from app.tools.base_tool import BaseTool


class HandTool(BaseTool):
    """Hand tool for panning. Handled specially by the viewport using
    canvas.scan_mark / scan_dragto with raw widget coordinates."""

    def on_press(self, x: float, y: float):
        pass

    def on_drag(self, x: float, y: float):
        pass

    def on_release(self, x: float, y: float):
        pass
