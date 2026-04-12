"""Markdown document implementing the Document ABC."""
from pathlib import Path
from app.core.document import Document
from app.core.obsidian.frontmatter import parse_frontmatter, serialize_frontmatter
from app.core.obsidian.wikilinks import extract_wikilinks


class MarkdownDocument(Document):
    def __init__(self):
        super().__init__()
        self._text: str = ""
        self._frontmatter: dict = {}
        self._original_text: str = ""

    @property
    def content_type(self) -> str:
        return "markdown"

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value
        self._modified = (value != self._original_text)

    @property
    def frontmatter(self) -> dict:
        return self._frontmatter

    @property
    def body(self) -> str:
        """Return text without frontmatter."""
        _, body = parse_frontmatter(self._text)
        return body

    @property
    def wikilinks(self) -> list[dict]:
        return extract_wikilinks(self._text)

    def open(self, file_path: str):
        self.close()
        path = Path(file_path)
        self._text = path.read_text(encoding='utf-8', errors='replace')
        self._original_text = self._text
        self._file_path = str(path.resolve())
        self._frontmatter, _ = parse_frontmatter(self._text)
        self._modified = False

    def save(self, file_path: str | None = None):
        save_path = file_path or self._file_path
        if not save_path:
            return
        Path(save_path).write_text(self._text, encoding='utf-8')
        self._file_path = save_path
        self._original_text = self._text
        self._modified = False

    def close(self):
        self._text = ""
        self._original_text = ""
        self._frontmatter = {}
        self._file_path = None
        self._modified = False

    def set_frontmatter(self, key: str, value):
        """Update a single frontmatter field."""
        self._frontmatter[key] = value
        body = self.body
        self._text = serialize_frontmatter(self._frontmatter, body)
        self._modified = True

    def new_document(self):
        """Create a new empty markdown document."""
        self.close()
        self._text = ""
        self._original_text = ""
        self._modified = False
