"""Dataclasses for the Vault → Notebook → Section → Page hierarchy."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Page:
    """A single note/page (.md file with frontmatter)."""
    path: Path
    title: str = ""
    created: str = ""
    modified: str = ""
    tags: list[str] = field(default_factory=list)
    pinned: bool = False
    is_sticky: bool = False
    sticky_color: str = "yellow"

    @property
    def name(self) -> str:
        return self.title or self.path.stem

    @property
    def exists(self) -> bool:
        return self.path.is_file()


@dataclass
class Section:
    """A section (subfolder within a notebook)."""
    path: Path
    name: str = ""
    sort_order: int = 0
    pages: list[Page] = field(default_factory=list)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def exists(self) -> bool:
        return self.path.is_dir()


@dataclass
class Notebook:
    """A notebook (top-level folder in the vault)."""
    path: Path
    name: str = ""
    color: str = "#007acc"
    sort_order: int = 0
    sections: list[Section] = field(default_factory=list)

    @property
    def section_count(self) -> int:
        return len(self.sections)

    @property
    def total_pages(self) -> int:
        return sum(s.page_count for s in self.sections)

    @property
    def exists(self) -> bool:
        return self.path.is_dir()
