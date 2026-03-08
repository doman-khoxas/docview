"""Multi-document manager with per-tab state."""
from dataclasses import dataclass
from pathlib import Path
from app.core.pdf_document import PDFDocument
from app.config import ZOOM_DEFAULT
from app.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TabState:
    pdf_doc: PDFDocument
    file_path: str | None = None
    scroll_y: float = 0.0
    zoom: float = ZOOM_DEFAULT
    active_tool_name: str | None = None


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
    def active_document(self) -> PDFDocument | None:
        tab = self.active_tab
        return tab.pdf_doc if tab else None

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
        for i, tab in enumerate(self._tabs):
            if tab.file_path and str(Path(tab.file_path).resolve()) == resolved:
                logger.debug("Document already open in tab %d, switching", i)
                self._active_index = i
                return i

        doc = PDFDocument()
        doc.open(file_path)
        tab = TabState(pdf_doc=doc, file_path=file_path)
        self._tabs.append(tab)
        self._active_index = len(self._tabs) - 1
        logger.info("Opened document in tab %d: %s", self._active_index, Path(file_path).name)
        return self._active_index

    def close_tab(self, index: int) -> bool:
        """Close a tab. Returns True if there are still tabs open."""
        if not (0 <= index < len(self._tabs)):
            return len(self._tabs) > 0

        tab = self._tabs[index]
        logger.info("Closing tab %d: %s", index, tab.pdf_doc.file_name)
        tab.pdf_doc.close()
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
        if tab:
            tab.scroll_y = scroll_y
            tab.zoom = zoom
            tab.active_tool_name = tool_name

    def has_unsaved_changes(self) -> bool:
        return any(tab.pdf_doc.modified for tab in self._tabs)
