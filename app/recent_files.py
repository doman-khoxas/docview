"""JSON persistence for recent files list."""
import json
from pathlib import Path
from app.config import RECENT_FILES_MAX


class RecentFiles:
    def __init__(self, path: str | None = None):
        if path is None:
            self._path = Path.home() / ".pdf_editor" / "recent_files.json"
        else:
            self._path = Path(path)
        self._files: list[str] = []
        self._load()

    def _load(self):
        try:
            if self._path.exists():
                with open(self._path, "r") as f:
                    data = json.load(f)
                self._files = [p for p in data if Path(p).exists()]
        except (json.JSONDecodeError, IOError):
            self._files = []

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._files, f, indent=2)

    def add(self, file_path: str):
        path = str(Path(file_path).resolve())
        if path in self._files:
            self._files.remove(path)
        self._files.insert(0, path)
        self._files = self._files[:RECENT_FILES_MAX]
        self._save()

    def get_all(self) -> list[str]:
        return list(self._files)

    def clear(self):
        self._files.clear()
        self._save()
