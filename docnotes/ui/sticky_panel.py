"""Extended sticky notes with section assignment for DocNotes."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import uuid
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QLabel, QPushButton, QSizeGrip, QComboBox, QMenu, QAction
)
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
from app.ui.theme import STICKY_COLORS
from app.core.obsidian.frontmatter import parse_frontmatter, serialize_frontmatter
from docnotes.config import STICKY_WIDTH, STICKY_HEIGHT, NOTE_AUTOSAVE_MS


class DocNotesSticky(QWidget):
    """Floating sticky note with section assignment."""

    save_requested = pyqtSignal(str)       # note_id
    close_requested = pyqtSignal(str)      # note_id
    convert_requested = pyqtSignal(str)    # note_id — convert to full page

    def __init__(self, note_id: str | None = None, sections: list[str] | None = None, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.note_id = note_id or str(uuid.uuid4())[:8]
        self._color_name = "yellow"
        self._section = ""
        self._drag_pos: QPoint | None = None
        self._created = datetime.now().isoformat()
        self._sections = sections or []

        self.resize(STICKY_WIDTH, STICKY_HEIGHT)
        self._setup_ui()

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(NOTE_AUTOSAVE_MS)
        self._save_timer.timeout.connect(lambda: self.save_requested.emit(self.note_id))

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        self._title_bar = QWidget()
        self._title_bar.setFixedHeight(28)
        self._title_bar.setCursor(QCursor(Qt.SizeAllCursor))
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(6, 0, 4, 0)
        title_layout.setSpacing(4)

        # Section assignment dropdown
        self._section_combo = QComboBox()
        self._section_combo.setFixedHeight(20)
        self._section_combo.setMinimumWidth(100)
        self._section_combo.setMaximumWidth(160)
        self._section_combo.addItem("(unassigned)")
        for s in self._sections:
            self._section_combo.addItem(s)
        self._section_combo.currentTextChanged.connect(self._on_section_changed)
        self._section_combo.setStyleSheet(
            "QComboBox { font-size: 9px; background: rgba(0,0,0,0.15); border: none; padding: 1px 4px; }"
        )
        title_layout.addWidget(self._section_combo)
        title_layout.addStretch()

        # Color buttons
        for name in ["yellow", "blue", "green", "pink", "orange", "purple"]:
            btn = QPushButton()
            btn.setFixedSize(12, 12)
            btn.setStyleSheet(
                f"background-color: {STICKY_COLORS[name]}; border: 1px solid #999; border-radius: 6px;"
            )
            btn.clicked.connect(lambda _, n=name: self.set_color(n))
            title_layout.addWidget(btn)

        # More menu button
        more_btn = QPushButton("\u22ee")
        more_btn.setFixedSize(20, 20)
        more_btn.setStyleSheet("background: transparent; border: none; font-size: 14px; color: #666;")
        more_btn.clicked.connect(self._show_more_menu)
        title_layout.addWidget(more_btn)

        # Close button
        close_btn = QPushButton("\u00d7")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("background: transparent; border: none; font-size: 14px; color: #666;")
        close_btn.clicked.connect(lambda: self.close_requested.emit(self.note_id))
        title_layout.addWidget(close_btn)

        layout.addWidget(self._title_bar)

        # Text area
        self._editor = QPlainTextEdit()
        self._editor.setFont(QFont("Segoe UI", 10))
        self._editor.setFrameShape(0)
        self._editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._editor)

        # Size grip
        grip = QSizeGrip(self)
        grip.setFixedSize(14, 14)
        layout.addWidget(grip, alignment=Qt.AlignRight)

        self.set_color("yellow")

    def _show_more_menu(self):
        menu = QMenu(self)
        menu.addAction("Convert to Page", lambda: self.convert_requested.emit(self.note_id))
        btn = self.sender()
        menu.exec_(btn.mapToGlobal(btn.rect().bottomLeft()))

    def set_color(self, color_name: str):
        self._color_name = color_name
        bg = STICKY_COLORS.get(color_name, STICKY_COLORS["yellow"])
        self._title_bar.setStyleSheet(f"background-color: {bg};")
        self._editor.setStyleSheet(
            f"background-color: {bg}; color: #333; border: none; padding: 4px;"
        )

    def update_sections(self, sections: list[str]):
        self._sections = sections
        current = self._section_combo.currentText()
        self._section_combo.blockSignals(True)
        self._section_combo.clear()
        self._section_combo.addItem("(unassigned)")
        for s in sections:
            self._section_combo.addItem(s)
        idx = self._section_combo.findText(current)
        if idx >= 0:
            self._section_combo.setCurrentIndex(idx)
        self._section_combo.blockSignals(False)

    def _on_section_changed(self, text: str):
        self._section = "" if text == "(unassigned)" else text
        self.save_requested.emit(self.note_id)

    @property
    def section(self) -> str:
        return self._section

    @section.setter
    def section(self, value: str):
        self._section = value
        idx = self._section_combo.findText(value or "(unassigned)")
        if idx >= 0:
            self._section_combo.setCurrentIndex(idx)

    @property
    def color_name(self) -> str:
        return self._color_name

    @property
    def text(self) -> str:
        return self._editor.toPlainText()

    @text.setter
    def text(self, value: str):
        self._editor.blockSignals(True)
        self._editor.setPlainText(value)
        self._editor.blockSignals(False)

    @property
    def created(self) -> str:
        return self._created

    @created.setter
    def created(self, value: str):
        self._created = value

    @property
    def note_metadata(self) -> dict:
        return {
            'title': '',
            'sticky': True,
            'section': self._section,
            'color': self._color_name,
            'x': self.x(),
            'y': self.y(),
            'width': self.width(),
            'height': self.height(),
            'created': self._created,
            'modified': datetime.now().isoformat(),
        }

    def _on_text_changed(self):
        self._save_timer.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._title_bar.geometry().contains(event.pos()):
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self.save_requested.emit(self.note_id)


class DocNotesStickyManager:
    """Manages DocNotes sticky notes with vault-aware persistence."""

    def __init__(self, vault_root: Path, sections: list[str]):
        self._vault_root = vault_root
        self._sticky_dir = vault_root / "_sticky"
        self._sticky_dir.mkdir(parents=True, exist_ok=True)
        self._notes: dict[str, DocNotesSticky] = {}
        self._sections = sections

    def load_all(self):
        for md in self._sticky_dir.glob("*.md"):
            try:
                text = md.read_text(encoding='utf-8')
                fm, body = parse_frontmatter(text)
                if not fm.get('sticky', False):
                    continue
                note_id = md.stem
                note = DocNotesSticky(note_id=note_id, sections=self._sections)
                note.text = body.strip()
                note.created = fm.get('created', '')
                note.section = fm.get('section', '')
                if 'x' in fm and 'y' in fm:
                    note.move(int(fm['x']), int(fm['y']))
                if 'width' in fm and 'height' in fm:
                    note.resize(int(fm['width']), int(fm['height']))
                if 'color' in fm:
                    note.set_color(fm['color'])
                note.save_requested.connect(self._on_save)
                note.close_requested.connect(self._on_close)
                note.convert_requested.connect(self._on_convert)
                self._notes[note_id] = note
                note.show()
            except Exception:
                continue

    def create_note(self, section: str = "", color: str = "yellow") -> DocNotesSticky:
        note = DocNotesSticky(sections=self._sections)
        note.section = section
        note.set_color(color)
        note.save_requested.connect(self._on_save)
        note.close_requested.connect(self._on_close)
        note.convert_requested.connect(self._on_convert)
        self._notes[note.note_id] = note
        self._save_note(note.note_id)
        note.show()
        return note

    def update_sections(self, sections: list[str]):
        self._sections = sections
        for note in self._notes.values():
            note.update_sections(sections)

    def _on_save(self, note_id: str):
        self._save_note(note_id)

    def _on_close(self, note_id: str):
        note = self._notes.pop(note_id, None)
        if note:
            note.hide()
            note.deleteLater()
            path = self._sticky_dir / f"{note_id}.md"
            if path.exists():
                path.unlink()

    def _on_convert(self, note_id: str):
        """Signal handler — actual conversion done by main window."""
        pass  # Wired externally

    def _save_note(self, note_id: str):
        note = self._notes.get(note_id)
        if not note:
            return
        metadata = note.note_metadata
        body = note.text
        text = serialize_frontmatter(metadata, body)
        path = self._sticky_dir / f"{note_id}.md"
        path.write_text(text, encoding='utf-8')

    def get_note(self, note_id: str) -> DocNotesSticky | None:
        return self._notes.get(note_id)

    def show_all(self):
        for note in self._notes.values():
            note.show()
            note.raise_()

    def hide_all(self):
        for note in self._notes.values():
            note.hide()
