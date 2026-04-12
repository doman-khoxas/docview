"""Multi-document manager with per-tab state, supporting PDF and Markdown."""
from dataclasses import dataclass, field
from pathlib import Path
from app.core.document import Document
from app.core.pdf_document import PDFDocument
from app.core.command import CommandStack
from app.config import ZOOM_DEFAULT, MARKDOWN_EXTENSIONS, PDF_EXTENSIONS


@dataclass
class TabState:
    document: Document
    file_path: str | None = None
    command_stack: CommandStack = field(default_factory=CommandStack)
    # PDF-specific viewport state
    scroll_y: float = 0.0
    zoom: float = ZOOM_DEFAULT
    active_tool_name: str | None = None
    # Markdown-specific state
    cursor_position: int = 0
    scroll_offset: int = 0


class DocumentManager:
    def __init__(self):
        self._tabs: list[TabState] = []
        self._active_index: int = -1

    @property
    def active_tab(self) -> TabState | None:
        if 0 <= self._active_index < len(self._tabs):
            return self._tabs[self._active_index]
        return None

    @property
    def active_document(self) -> Document | None:
        tab = self.active_tab
        return tab.document if tab else None

    @property
    def active_index(self) -> int:
        return self._active_index

    @property
    def tab_count(self) -> int:
        return len(self._tabs)

    def get_tab(self, index: int) -> TabState | None:
        if 0 <= index < len(self._tabs):
            return self._tabs[index]
        return None

    def get_all_tabs(self) -> list[TabState]:
        return list(self._tabs)

    def open_document(self, file_path: str) -> int:
        """Open a document in a new tab. Returns the tab index."""
        resolved = str(Path(file_path).resolve())

        # Check if already open
        for i, tab in enumerate(self._tabs):
            if tab.file_path and str(Path(tab.file_path).resolve()) == resolved:
                self._active_index = i
                return i

        # Create appropriate document type
        suffix = Path(file_path).suffix.lower()
        if suffix in MARKDOWN_EXTENSIONS:
            from app.core.markdown_document import MarkdownDocument
            doc = MarkdownDocument()
        elif suffix in PDF_EXTENSIONS:
            doc = PDFDocument()
        else:
            # Default to markdown for text files
            from app.core.markdown_document import MarkdownDocument
            doc = MarkdownDocument()

        doc.open(file_path)
        tab = TabState(document=doc, file_path=file_path)
        self._tabs.append(tab)
        self._active_index = len(self._tabs) - 1
        return self._active_index

    def close_tab(self, index: int) -> bool:
        """Close a tab. Returns True if there are still tabs open."""
        if not (0 <= index < len(self._tabs)):
            return len(self._tabs) > 0

        tab = self._tabs[index]
        tab.document.close()
        self._tabs.pop(index)

        if len(self._tabs) == 0:
            self._active_index = -1
        elif self._active_index >= len(self._tabs):
            self._active_index = len(self._tabs) - 1
        elif self._active_index > index:
            self._active_index -= 1

        return len(self._tabs) > 0

    def switch_tab(self, index: int):
        if 0 <= index < len(self._tabs):
            self._active_index = index

    def save_viewport_state(self, scroll_y: float, zoom: float, tool_name: str | None):
        tab = self.active_tab
        if tab and tab.document.content_type == "pdf":
            tab.scroll_y = scroll_y
            tab.zoom = zoom
            tab.active_tool_name = tool_name

    def save_editor_state(self, cursor_position: int, scroll_offset: int):
        tab = self.active_tab
        if tab and tab.document.content_type == "markdown":
            tab.cursor_position = cursor_position
            tab.scroll_offset = scroll_offset

    def has_unsaved_changes(self) -> bool:
        return any(tab.document.modified for tab in self._tabs)
