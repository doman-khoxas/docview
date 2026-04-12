"""DocNotes vault — manages the Notebook → Section → Page hierarchy on disk."""
import yaml
from pathlib import Path
from datetime import datetime
from docnotes.config import (
    VAULT_META_FILE, NOTEBOOK_META_FILE, SECTION_META_FILE,
    STICKY_DIR_NAME, NOTEBOOK_COLORS, DEFAULT_NOTE_TITLE
)
from docnotes.core.notebook import Notebook, Section, Page

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.core.obsidian.frontmatter import parse_frontmatter, serialize_frontmatter


class Vault:
    """Manages the on-disk vault structure."""

    def __init__(self, root: str):
        self._root = Path(root)
        self._notebooks: list[Notebook] = []

    @property
    def root(self) -> Path:
        return self._root

    @property
    def notebooks(self) -> list[Notebook]:
        return self._notebooks

    @property
    def name(self) -> str:
        meta = self._read_vault_meta()
        return meta.get('name', self._root.name)

    # ── Initialization ──

    def ensure_exists(self):
        """Create vault directory and metadata if they don't exist."""
        self._root.mkdir(parents=True, exist_ok=True)
        meta_path = self._root / VAULT_META_FILE
        if not meta_path.exists():
            meta = {
                'name': 'My Notes',
                'created': datetime.now().isoformat(),
                'version': '1.0',
            }
            meta_path.write_text(yaml.dump(meta, default_flow_style=False), encoding='utf-8')

        # Ensure sticky directory exists
        (self._root / STICKY_DIR_NAME).mkdir(exist_ok=True)

    def scan(self):
        """Scan the vault directory and build the hierarchy."""
        self._notebooks.clear()
        if not self._root.is_dir():
            return

        for entry in sorted(self._root.iterdir()):
            if entry.is_dir() and not entry.name.startswith('_') and not entry.name.startswith('.'):
                notebook = self._scan_notebook(entry)
                self._notebooks.append(notebook)

    def _scan_notebook(self, path: Path) -> Notebook:
        meta = self._read_yaml(path / NOTEBOOK_META_FILE)
        nb = Notebook(
            path=path,
            name=meta.get('name', path.name),
            color=meta.get('color', NOTEBOOK_COLORS[len(self._notebooks) % len(NOTEBOOK_COLORS)]),
            sort_order=meta.get('sort_order', 0),
        )

        for entry in sorted(path.iterdir()):
            if entry.is_dir() and not entry.name.startswith('_') and not entry.name.startswith('.'):
                section = self._scan_section(entry)
                nb.sections.append(section)

        return nb

    def _scan_section(self, path: Path) -> Section:
        meta = self._read_yaml(path / SECTION_META_FILE)
        section = Section(
            path=path,
            name=meta.get('name', path.name),
            sort_order=meta.get('sort_order', 0),
        )

        for md_file in sorted(path.glob('*.md')):
            page = self._scan_page(md_file)
            section.pages.append(page)

        return section

    def _scan_page(self, path: Path) -> Page:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
            fm, _ = parse_frontmatter(text)
        except OSError:
            fm = {}

        return Page(
            path=path,
            title=fm.get('title', path.stem),
            created=fm.get('created', ''),
            modified=fm.get('modified', ''),
            tags=fm.get('tags', []) or [],
            pinned=fm.get('pinned', False),
            is_sticky=fm.get('sticky', False),
            sticky_color=fm.get('color', 'yellow'),
        )

    # ── CRUD Operations ──

    def create_notebook(self, name: str, color: str = "") -> Notebook:
        path = self._root / self._safe_name(name)
        path.mkdir(exist_ok=True)
        color = color or NOTEBOOK_COLORS[len(self._notebooks) % len(NOTEBOOK_COLORS)]
        meta = {'name': name, 'color': color, 'sort_order': len(self._notebooks)}
        (path / NOTEBOOK_META_FILE).write_text(yaml.dump(meta), encoding='utf-8')
        nb = Notebook(path=path, name=name, color=color, sort_order=len(self._notebooks))
        self._notebooks.append(nb)
        return nb

    def create_section(self, notebook: Notebook, name: str) -> Section:
        path = notebook.path / self._safe_name(name)
        path.mkdir(exist_ok=True)
        meta = {'name': name, 'sort_order': len(notebook.sections)}
        (path / SECTION_META_FILE).write_text(yaml.dump(meta), encoding='utf-8')
        section = Section(path=path, name=name, sort_order=len(notebook.sections))
        notebook.sections.append(section)
        return section

    def create_page(self, section: Section, title: str = "") -> Page:
        title = title or DEFAULT_NOTE_TITLE
        filename = self._safe_name(title) + '.md'
        path = section.path / filename

        # Avoid collisions
        counter = 1
        while path.exists():
            path = section.path / f"{self._safe_name(title)}_{counter}.md"
            counter += 1

        now = datetime.now().isoformat()
        fm = {
            'title': title,
            'created': now,
            'modified': now,
            'tags': [],
            'pinned': False,
        }
        text = serialize_frontmatter(fm, '\n')
        path.write_text(text, encoding='utf-8')

        page = Page(path=path, title=title, created=now, modified=now)
        section.pages.append(page)
        return page

    def create_sticky(self, section_path: str = "", color: str = "yellow") -> Page:
        """Create a sticky note in the _sticky directory."""
        import uuid
        sticky_dir = self._root / STICKY_DIR_NAME
        sticky_dir.mkdir(exist_ok=True)
        note_id = str(uuid.uuid4())[:8]
        path = sticky_dir / f"{note_id}.md"

        now = datetime.now().isoformat()
        fm = {
            'title': '',
            'sticky': True,
            'section': section_path,
            'color': color,
            'x': 100,
            'y': 100,
            'width': 280,
            'height': 280,
            'created': now,
            'modified': now,
        }
        text = serialize_frontmatter(fm, '\n')
        path.write_text(text, encoding='utf-8')

        return Page(path=path, title='', created=now, modified=now,
                    is_sticky=True, sticky_color=color)

    def delete_page(self, section: Section, page: Page):
        if page.path.exists():
            page.path.unlink()
        if page in section.pages:
            section.pages.remove(page)

    def delete_section(self, notebook: Notebook, section: Section):
        import shutil
        if section.path.exists():
            shutil.rmtree(section.path)
        if section in notebook.sections:
            notebook.sections.remove(section)

    def delete_notebook(self, notebook: Notebook):
        import shutil
        if notebook.path.exists():
            shutil.rmtree(notebook.path)
        if notebook in self._notebooks:
            self._notebooks.remove(notebook)

    def get_all_stickies(self) -> list[Page]:
        """Get all sticky notes from _sticky directory."""
        sticky_dir = self._root / STICKY_DIR_NAME
        if not sticky_dir.is_dir():
            return []
        pages = []
        for md in sticky_dir.glob('*.md'):
            pages.append(self._scan_page(md))
        return pages

    def get_section_path(self, notebook: Notebook, section: Section) -> str:
        """Get the relative section path (e.g., 'Work/Collins')."""
        return f"{notebook.name}/{section.name}"

    def find_section_by_path(self, section_path: str) -> tuple[Notebook, Section] | None:
        """Find a notebook and section by path like 'Work/Collins'."""
        parts = section_path.split('/', 1)
        if len(parts) != 2:
            return None
        nb_name, sec_name = parts
        for nb in self._notebooks:
            if nb.name == nb_name:
                for sec in nb.sections:
                    if sec.name == sec_name:
                        return nb, sec
        return None

    def search_pages(self, query: str) -> list[Page]:
        """Search all pages by title and content."""
        query_lower = query.lower()
        results = []
        for nb in self._notebooks:
            for sec in nb.sections:
                for page in sec.pages:
                    if query_lower in page.title.lower():
                        results.append(page)
                        continue
                    try:
                        text = page.path.read_text(encoding='utf-8', errors='replace')
                        if query_lower in text.lower():
                            results.append(page)
                    except OSError:
                        pass
        return results

    # ── Helpers ──

    def _read_vault_meta(self) -> dict:
        return self._read_yaml(self._root / VAULT_META_FILE)

    @staticmethod
    def _read_yaml(path: Path) -> dict:
        if path.exists():
            try:
                return yaml.safe_load(path.read_text(encoding='utf-8')) or {}
            except (yaml.YAMLError, OSError):
                pass
        return {}

    @staticmethod
    def _safe_name(name: str) -> str:
        """Sanitize a name for use as a filename/directory."""
        import re
        safe = re.sub(r'[<>:"/\\|?*]', '', name).strip()
        return safe or 'untitled'
