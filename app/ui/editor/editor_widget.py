"""Combined markdown editor + preview widget with view mode control."""
from PyQt5.QtWidgets import (
    QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QAction, QActionGroup, QLabel, QToolButton
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QKeySequence
from app.ui.editor.markdown_editor import MarkdownEditor
from app.ui.editor.markdown_preview import MarkdownPreview
from app.ui.theme import BG_SURFACE, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT


class ViewMode:
    PREVIEW = "preview"   # Read-only rendered view (default)
    SPLIT = "split"       # Editor + preview side by side
    EDIT = "edit"         # Editor only, no preview


class EditorWidget(QWidget):
    """Markdown viewer/editor with switchable view modes.

    Default: preview-only (non-editable rendered view).
    User can switch to split (editor + preview) or edit-only.
    """

    wikilink_clicked = pyqtSignal(str)
    content_modified = pyqtSignal()
    view_mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._document = None
        self._mode = ViewMode.PREVIEW

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── View mode toolbar ──
        self._view_bar = QWidget()
        self._view_bar.setFixedHeight(34)
        self._view_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_SURFACE};
                border-bottom: 1px solid {BORDER};
            }}
        """)
        bar_layout = QHBoxLayout(self._view_bar)
        bar_layout.setContentsMargins(8, 0, 8, 0)
        bar_layout.setSpacing(2)

        # File type indicator
        self._file_label = QLabel("Markdown")
        self._file_label.setFont(QFont("Segoe UI", 9))
        self._file_label.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        bar_layout.addWidget(self._file_label)

        bar_layout.addStretch()

        # View mode buttons
        self._mode_group = QActionGroup(self)
        self._mode_group.setExclusive(True)

        self._btn_preview = self._make_mode_btn("Preview", ViewMode.PREVIEW, True)
        bar_layout.addWidget(self._btn_preview)

        self._btn_split = self._make_mode_btn("Split", ViewMode.SPLIT, False)
        bar_layout.addWidget(self._btn_split)

        self._btn_edit = self._make_mode_btn("Edit", ViewMode.EDIT, False)
        bar_layout.addWidget(self._btn_edit)

        bar_layout.addStretch()

        # Word count
        self._word_count = QLabel("")
        self._word_count.setFont(QFont("Segoe UI", 9))
        self._word_count.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none;")
        bar_layout.addWidget(self._word_count)

        layout.addWidget(self._view_bar)

        # ── Content area ──
        self._splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self._splitter)

        # Editor (left in split mode)
        self._editor = MarkdownEditor()
        self._editor.text_changed_signal.connect(self._on_text_changed)
        self._splitter.addWidget(self._editor)

        # Preview (right in split mode, full in preview mode)
        self._preview = MarkdownPreview()
        self._preview.wikilink_clicked.connect(self.wikilink_clicked.emit)
        self._splitter.addWidget(self._preview)

        self._splitter.setSizes([500, 500])

        # Debounce preview updates
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(300)
        self._preview_timer.timeout.connect(self._update_preview)

        # Start in preview mode
        self._apply_mode(ViewMode.PREVIEW)

    def _make_mode_btn(self, label: str, mode: str, checked: bool) -> QToolButton:
        btn = QToolButton()
        btn.setText(label)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setAutoExclusive(True)
        btn.setFixedHeight(26)
        btn.setMinimumWidth(65)
        btn.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 2px 10px;
                color: {TEXT_SECONDARY};
                font-size: 11px;
            }}
            QToolButton:hover {{
                background-color: #2a2d2e;
                color: {TEXT_PRIMARY};
            }}
            QToolButton:checked {{
                background-color: {ACCENT};
                color: #ffffff;
                border-color: {ACCENT};
            }}
        """)
        btn.clicked.connect(lambda: self.set_view_mode(mode))
        return btn

    # ── View mode control ──

    def set_view_mode(self, mode: str):
        if mode == self._mode:
            return
        self._mode = mode
        self._apply_mode(mode)
        self.view_mode_changed.emit(mode)

    def _apply_mode(self, mode: str):
        if mode == ViewMode.PREVIEW:
            self._editor.hide()
            self._preview.show()
            self._btn_preview.setChecked(True)
        elif mode == ViewMode.SPLIT:
            self._editor.show()
            self._preview.show()
            self._splitter.setSizes([500, 500])
            self._btn_split.setChecked(True)
        elif mode == ViewMode.EDIT:
            self._editor.show()
            self._preview.hide()
            self._btn_edit.setChecked(True)

    @property
    def view_mode(self) -> str:
        return self._mode

    # ── Document loading ──

    def load_document(self, md_doc):
        """Load a MarkdownDocument. Opens in preview mode by default."""
        self._document = md_doc
        self._editor.set_text(md_doc.text)
        self._update_preview()
        self._update_word_count()
        self._file_label.setText(md_doc.file_name)
        # Always open in preview mode
        self.set_view_mode(ViewMode.PREVIEW)

    # ── Text handling ──

    def _on_text_changed(self):
        if self._document:
            self._document.text = self._editor.get_text()
            self.content_modified.emit()
        self._preview_timer.start()
        self._update_word_count()

    def _update_preview(self):
        text = self._editor.get_text()
        self._preview.update_preview(text)

    def _update_word_count(self):
        text = self._editor.get_text()
        words = len(text.split()) if text.strip() else 0
        lines = text.count('\n') + 1 if text else 0
        self._word_count.setText(f"{words} words  {lines} lines")

    # ── Cursor/scroll state ──

    def get_cursor_position(self) -> int:
        return self._editor.textCursor().position()

    def set_cursor_position(self, pos: int):
        cursor = self._editor.textCursor()
        cursor.setPosition(min(pos, len(self._editor.get_text())))
        self._editor.setTextCursor(cursor)

    def get_scroll_offset(self) -> int:
        return self._editor.verticalScrollBar().value()

    def set_scroll_offset(self, offset: int):
        self._editor.verticalScrollBar().setValue(offset)
