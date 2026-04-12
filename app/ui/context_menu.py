"""Right-click context menu on the viewport."""
from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import pyqtSignal


class ViewportContextMenu(QMenu):
    """Context menu for the PDF viewport."""

    tool_requested = pyqtSignal(str)
    action_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.addAction("Zoom In", lambda: self.action_requested.emit("zoom_in"))
        self.addAction("Zoom Out", lambda: self.action_requested.emit("zoom_out"))
        self.addAction("Fit Width", lambda: self.action_requested.emit("fit_width"))
        self.addSeparator()
        self.addAction("Hand Tool", lambda: self.tool_requested.emit("hand"))
        self.addAction("Select", lambda: self.tool_requested.emit("select"))
        self.addAction("Highlight", lambda: self.tool_requested.emit("highlight"))
        self.addAction("Rectangle", lambda: self.tool_requested.emit("rect"))
        self.addAction("Text", lambda: self.tool_requested.emit("text"))
        self.addSeparator()
        self.addAction("Rotate Page", lambda: self.action_requested.emit("rotate_cw"))
        self.addAction("Delete Page", lambda: self.action_requested.emit("delete_page"))
