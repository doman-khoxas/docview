"""QPlainTextEdit with line numbers for markdown editing."""
from PyQt5.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt5.QtGui import (
    QColor, QPainter, QFont, QTextFormat, QTextCursor, QPalette
)
from app.config import MD_FONT_FAMILY, MD_FONT_SIZE, MD_LINE_NUMBER_BG, MD_LINE_NUMBER_FG
from app.ui.editor.markdown_highlighter import MarkdownHighlighter


class LineNumberArea(QWidget):
    """Widget that displays line numbers alongside the editor."""

    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.line_number_area_paint(event)


class MarkdownEditor(QPlainTextEdit):
    """Code-editor-style markdown text editor with line numbers."""

    text_changed_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Font
        font = QFont(MD_FONT_FAMILY, MD_FONT_SIZE)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)

        # Line numbers
        self._line_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_area_width)
        self.updateRequest.connect(self._update_line_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self._update_line_area_width(0)

        # Syntax highlighting
        self._highlighter = MarkdownHighlighter(self.document())

        # Style
        self.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                selection-background-color: #264f78;
            }
        """)

        # Emit on text change
        self.textChanged.connect(self.text_changed_signal.emit)

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        space = 12 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def _update_line_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_area(self, rect, dy):
        if dy:
            self._line_area.scroll(0, dy)
        else:
            self._line_area.update(0, rect.y(), self._line_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_area.setGeometry(QRect(cr.left(), cr.top(),
                                          self.line_number_area_width(), cr.height()))

    def line_number_area_paint(self, event):
        painter = QPainter(self._line_area)
        painter.fillRect(event.rect(), QColor(MD_LINE_NUMBER_BG))
        painter.setPen(QColor(MD_LINE_NUMBER_FG))
        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(0, top, self._line_area.width() - 4,
                                 self.fontMetrics().height(),
                                 Qt.AlignRight, str(block_number + 1))
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

        painter.end()

    def _highlight_current_line(self):
        selections = []
        if not self.isReadOnly():
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(QColor("#2a2d2e"))
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            selections.append(sel)
        self.setExtraSelections(selections)

    def get_text(self) -> str:
        return self.toPlainText()

    def set_text(self, text: str):
        self.blockSignals(True)
        self.setPlainText(text)
        self.blockSignals(False)
