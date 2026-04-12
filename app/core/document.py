"""Abstract base class for all document types."""
from abc import ABC, abstractmethod
from pathlib import Path


class Document(ABC):
    """Base class that PDF, Markdown, and other document types implement."""

    def __init__(self):
        self._file_path: str | None = None
        self._modified: bool = False

    @property
    def file_path(self) -> str | None:
        return self._file_path

    @property
    def file_name(self) -> str:
        if self._file_path:
            return Path(self._file_path).name
        return "Untitled"

    @property
    def is_open(self) -> bool:
        return True

    @property
    def modified(self) -> bool:
        return self._modified

    @modified.setter
    def modified(self, value: bool):
        self._modified = value

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Return 'pdf', 'markdown', etc."""
        ...

    @abstractmethod
    def open(self, file_path: str):
        ...

    @abstractmethod
    def save(self, file_path: str | None = None):
        ...

    @abstractmethod
    def close(self):
        ...
