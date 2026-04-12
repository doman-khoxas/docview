"""Manages sticky note lifecycle: create, persist, restore."""
import yaml
from pathlib import Path
from PyQt5.QtCore import QObject
from app.config import STICKY_NOTE_DIR
from app.ui.sticky.sticky_note import StickyNote
from app.core.obsidian.frontmatter import parse_frontmatter, serialize_frontmatter


class StickyManager(QObject):
    """Manages all sticky notes — persistence to ~/.docview/sticky-notes/*.md."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._notes: dict[str, StickyNote] = {}
        self._storage_dir = Path.home() / STICKY_NOTE_DIR
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_all()

    def _load_all(self):
        """Restore sticky notes from disk."""
        for md_file in self._storage_dir.glob("*.md"):
            try:
                text = md_file.read_text(encoding='utf-8')
                fm, body = parse_frontmatter(text)
                note_id = fm.get('id', md_file.stem)
                note = StickyNote(note_id=note_id)
                note.text = body.strip()
                note.created = fm.get('created', '')

                # Restore position and size
                if 'x' in fm and 'y' in fm:
                    note.move(int(fm['x']), int(fm['y']))
                if 'width' in fm and 'height' in fm:
                    note.resize(int(fm['width']), int(fm['height']))
                if 'color' in fm:
                    note.set_color(fm['color'])

                note.save_requested.connect(self._on_save)
                note.close_requested.connect(self._on_close)
                self._notes[note_id] = note
                note.show()
            except Exception:
                continue

    def create_note(self) -> StickyNote:
        """Create a new sticky note."""
        note = StickyNote()
        note.save_requested.connect(self._on_save)
        note.close_requested.connect(self._on_close)
        self._notes[note.note_id] = note
        note.show()
        self._save_note(note.note_id)
        return note

    def _on_save(self, note_id: str):
        self._save_note(note_id)

    def _on_close(self, note_id: str):
        note = self._notes.get(note_id)
        if note:
            note.hide()
            note.deleteLater()
            del self._notes[note_id]
            # Remove file
            path = self._storage_dir / f"{note_id}.md"
            if path.exists():
                path.unlink()

    def _save_note(self, note_id: str):
        """Persist a note to disk as .md with YAML frontmatter."""
        note = self._notes.get(note_id)
        if not note:
            return

        metadata = note.note_metadata
        body = note.text
        text = serialize_frontmatter(metadata, body)

        path = self._storage_dir / f"{note_id}.md"
        path.write_text(text, encoding='utf-8')

    def show_all(self):
        for note in self._notes.values():
            note.show()
            note.raise_()

    def hide_all(self):
        for note in self._notes.values():
            note.hide()

    def save_all(self):
        for note_id in self._notes:
            self._save_note(note_id)

    @property
    def count(self) -> int:
        return len(self._notes)
