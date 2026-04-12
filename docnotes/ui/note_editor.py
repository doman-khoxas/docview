"""Note editor wrapper — reuses EditorWidget with DocNotes-specific toolbar."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from app.ui.editor.editor_widget import EditorWidget
from app.ui.theme import TEXT_SECONDARY, BG_SURFACE
from docnotes.core.note_document import NoteDocument
from docnotes.config import NOTE_AUTOSAVE_MS


class NoteEditor(QWidget):
    """Wraps EditorWidget with auto-save and DocNotes metadata."""

    content_saved = pyqtSignal()
    wikilink_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._document: NoteDocument | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Editor
        self._editor = EditorWidget()
        self._editor.content_modified.connect(self._on_modified)
        self._editor.wikilink_clicked.connect(self.wikilink_clicked.emit)
        layout.addWidget(self._editor)

        # Empty state
        self._empty = QLabel("Select a note to view")
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setFont(QFont("Segoe UI", 14, QFont.Light))
        self._empty.setStyleSheet(f"color: {TEXT_SECONDARY};")
        layout.addWidget(self._empty)

        # Auto-save timer
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(NOTE_AUTOSAVE_MS)
        self._save_timer.timeout.connect(self._auto_save)

        self._show_empty()

    def load_note(self, page):
        """Load a page into the editor."""
        doc = NoteDocument()
        doc.open(str(page.path))
        self._document = doc

        self._empty.hide()
        self._editor.show()
        self._editor.load_document(doc)

    def _show_empty(self):
        self._editor.hide()
        self._empty.show()
        self._document = None

    def clear(self):
        self._show_empty()

    def _on_modified(self):
        self._save_timer.start()

    def _auto_save(self):
        if self._document and self._document.modified:
            self._document.touch_modified()
            self._document.save()
            self.content_saved.emit()
