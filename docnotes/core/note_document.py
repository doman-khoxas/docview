"""NoteDocument — extends MarkdownDocument with section and tag awareness."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from datetime import datetime
from app.core.markdown_document import MarkdownDocument


class NoteDocument(MarkdownDocument):
    """A note with section assignment, tags, and sticky support."""

    @property
    def title(self) -> str:
        return self.frontmatter.get('title', self.file_name.replace('.md', ''))

    @title.setter
    def title(self, value: str):
        self.set_frontmatter('title', value)

    @property
    def tags(self) -> list[str]:
        return self.frontmatter.get('tags', []) or []

    @tags.setter
    def tags(self, value: list[str]):
        self.set_frontmatter('tags', value)

    @property
    def section(self) -> str:
        return self.frontmatter.get('section', '')

    @section.setter
    def section(self, value: str):
        self.set_frontmatter('section', value)

    @property
    def pinned(self) -> bool:
        return self.frontmatter.get('pinned', False)

    @pinned.setter
    def pinned(self, value: bool):
        self.set_frontmatter('pinned', value)

    @property
    def is_sticky(self) -> bool:
        return self.frontmatter.get('sticky', False)

    @property
    def sticky_color(self) -> str:
        return self.frontmatter.get('color', 'yellow')

    def touch_modified(self):
        """Update the modified timestamp."""
        self.set_frontmatter('modified', datetime.now().isoformat())
