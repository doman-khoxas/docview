"""Obsidian vault integration -- file indexing, wikilink resolution, change detection."""
import json
from pathlib import Path
from PyQt5.QtCore import QFileSystemWatcher, QObject, pyqtSignal
from app.core.obsidian.wikilinks import extract_wikilinks, find_backlinks


class ObsidianVault(QObject):
    """Manages an Obsidian vault: file index, wikilink resolution, file watching."""

    files_changed = pyqtSignal()

    def __init__(self, vault_path: str, parent=None):
        super().__init__(parent)
        self._vault_path = Path(vault_path)
        self._file_index: dict[str, str] = {}  # lowercase name -> absolute path
        self._watcher: QFileSystemWatcher | None = None

        if self._vault_path.is_dir():
            self._build_index()
            self._setup_watcher()

    @property
    def vault_path(self) -> str:
        return str(self._vault_path)

    @property
    def is_valid(self) -> bool:
        return self._vault_path.is_dir()

    @property
    def file_count(self) -> int:
        return len(self._file_index)

    def _build_index(self):
        """Scan vault and build name-to-path index."""
        self._file_index.clear()
        for md_file in self._vault_path.rglob('*.md'):
            # Skip .obsidian directory
            if '.obsidian' in md_file.parts:
                continue
            key = md_file.stem.lower()
            # Prefer shorter paths (closer to vault root)
            existing = self._file_index.get(key)
            if existing is None or len(str(md_file)) < len(existing):
                self._file_index[key] = str(md_file)

    def _setup_watcher(self):
        """Watch vault directory for changes."""
        self._watcher = QFileSystemWatcher([str(self._vault_path)], self)
        self._watcher.directoryChanged.connect(self._on_directory_changed)

    def _on_directory_changed(self, path: str):
        self._build_index()
        self.files_changed.emit()

    def resolve_link(self, target: str) -> str | None:
        """Resolve a wikilink target to an absolute file path."""
        key = target.lower()
        if not key.endswith('.md'):
            result = self._file_index.get(key)
            if result:
                return result
        # Try with .md stripped
        if key.endswith('.md'):
            key = key[:-3]
            return self._file_index.get(key)
        return None

    def get_backlinks(self, file_path: str) -> list[str]:
        """Get all files linking to the given file."""
        return find_backlinks(file_path, str(self._vault_path))

    def get_all_files(self) -> list[str]:
        """Return all markdown files in the vault."""
        return sorted(self._file_index.values())

    def search_files(self, query: str) -> list[str]:
        """Search for files by name."""
        query_lower = query.lower()
        results = []
        for name, path in self._file_index.items():
            if query_lower in name:
                results.append(path)
        return sorted(results)

    def get_vault_settings(self) -> dict:
        """Read .obsidian/app.json if it exists."""
        config = self._vault_path / '.obsidian' / 'app.json'
        if config.exists():
            try:
                return json.loads(config.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError):
                pass
        return {}
