"""Modern flat toolbar for DocView with tool buttons and actions."""
from PyQt5.QtWidgets import (
    QToolBar, QAction, QActionGroup, QToolButton, QMenu, QWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from app.ui.theme import ACCENT


class DocToolbar(QToolBar):
    """Flat dark toolbar with annotation tools and document actions."""

    tool_selected = pyqtSignal(str)  # tool name

    TOOL_ICONS = {
        "select": "\u25b3",      # triangle
        "hand": "\u270b",        # hand
        "text": "T",
        "highlight": "\u2591",   # light shade
        "rect": "\u25a1",        # square
        "circle": "\u25cb",      # circle
        "line": "\u2571",        # diagonal
        "freehand": "\u270e",    # pencil
        "redact": "\u2588",      # full block
        "image": "\U0001f5bc",   # framed picture
        "signature": "\u270d",   # writing hand
    }

    def __init__(self, parent=None):
        super().__init__("Tools", parent)
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(parent.size() if parent else None)

        self._tool_actions: dict[str, QAction] = {}
        self._tool_group = QActionGroup(self)
        self._tool_group.setExclusive(True)

        self._setup_tools()
        self.addSeparator()
        self._setup_document_actions()

    def _setup_tools(self):
        for name, icon_text in self.TOOL_ICONS.items():
            action = QAction(f"{icon_text}  {name.capitalize()}", self)
            action.setCheckable(True)
            action.setData(name)
            action.triggered.connect(lambda checked, n=name: self.tool_selected.emit(n))
            self._tool_group.addAction(action)
            self._tool_actions[name] = action
            self.addAction(action)

        # Default to select
        if "select" in self._tool_actions:
            self._tool_actions["select"].setChecked(True)

    def _setup_document_actions(self):
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)

        # Page operations dropdown
        page_btn = QToolButton(self)
        page_btn.setText("Page \u25bc")
        page_menu = QMenu(page_btn)
        page_menu.addAction("Rotate CW", lambda: self._emit_action("rotate_cw"))
        page_menu.addAction("Rotate CCW", lambda: self._emit_action("rotate_ccw"))
        page_menu.addSeparator()
        page_menu.addAction("Delete Page", lambda: self._emit_action("delete_page"))
        page_menu.addAction("Insert Blank Page", lambda: self._emit_action("insert_blank"))
        page_btn.setMenu(page_menu)
        page_btn.setPopupMode(QToolButton.InstantPopup)
        self.addWidget(page_btn)

        # Document operations dropdown
        doc_btn = QToolButton(self)
        doc_btn.setText("Document \u25bc")
        doc_menu = QMenu(doc_btn)
        doc_menu.addAction("Merge PDFs...", lambda: self._emit_action("merge"))
        doc_menu.addAction("Split PDF...", lambda: self._emit_action("split"))
        doc_menu.addSeparator()
        doc_menu.addAction("OCR Document...", lambda: self._emit_action("ocr"))
        doc_menu.addAction("Extract Text...", lambda: self._emit_action("extract_text"))
        doc_btn.setMenu(doc_menu)
        doc_btn.setPopupMode(QToolButton.InstantPopup)
        self.addWidget(doc_btn)

    def _emit_action(self, action_name: str):
        # Placeholder for wiring to main window actions
        parent = self.parent()
        if parent and hasattr(parent, 'handle_toolbar_action'):
            parent.handle_toolbar_action(action_name)

    def set_active_tool(self, tool_name: str | None):
        """Highlight the active tool button."""
        for name, action in self._tool_actions.items():
            action.setChecked(name == tool_name)
