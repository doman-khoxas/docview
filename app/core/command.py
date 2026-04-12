"""Undo/redo command system for DocView.

Uses the Command pattern: each undoable action is a Command object
with execute() and undo() methods, managed by a CommandStack per document.
"""
from abc import ABC, abstractmethod
from copy import deepcopy


class Command(ABC):
    """Base class for undoable commands."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for the Edit menu."""
        ...

    @abstractmethod
    def execute(self):
        """Perform the action."""
        ...

    @abstractmethod
    def undo(self):
        """Reverse the action."""
        ...

    def redo(self):
        """Re-perform after undo. Default: just call execute again."""
        self.execute()


class CommandStack:
    """Per-document undo/redo stack."""

    def __init__(self, max_size: int = 100):
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []
        self._max_size = max_size

    def push(self, command: Command):
        """Execute a command and push it onto the undo stack."""
        command.execute()
        self._undo_stack.append(command)
        if len(self._undo_stack) > self._max_size:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> Command | None:
        """Undo the last command. Returns the undone command or None."""
        if not self._undo_stack:
            return None
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        return cmd

    def redo(self) -> Command | None:
        """Redo the last undone command. Returns the redone command or None."""
        if not self._redo_stack:
            return None
        cmd = self._redo_stack.pop()
        cmd.redo()
        self._undo_stack.append(cmd)
        return cmd

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def undo_description(self) -> str:
        if self._undo_stack:
            return self._undo_stack[-1].description
        return ""

    @property
    def redo_description(self) -> str:
        if self._redo_stack:
            return self._redo_stack[-1].description
        return ""

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()


# ── Concrete commands ──


class AddAnnotationCommand(Command):
    """Add a pending annotation to a PDF document."""

    def __init__(self, pdf_doc, page_num: int, annotation):
        self._doc = pdf_doc
        self._page = page_num
        self._annot = annotation

    @property
    def description(self) -> str:
        return f"Add {type(self._annot).__name__}"

    def execute(self):
        self._doc.add_pending_annotation(self._page, self._annot)

    def undo(self):
        self._doc.remove_pending_annotation(self._page, self._annot)


class RemoveAnnotationCommand(Command):
    """Remove a pending annotation from a PDF document."""

    def __init__(self, pdf_doc, page_num: int, annotation):
        self._doc = pdf_doc
        self._page = page_num
        self._annot = annotation

    @property
    def description(self) -> str:
        return f"Delete {type(self._annot).__name__}"

    def execute(self):
        self._doc.remove_pending_annotation(self._page, self._annot)

    def undo(self):
        self._doc.add_pending_annotation(self._page, self._annot)


class MoveAnnotationCommand(Command):
    """Move an annotation by storing old and new attribute values."""

    def __init__(self, pdf_doc, page_num: int, annotation, old_attrs: dict, new_attrs: dict):
        self._doc = pdf_doc
        self._page = page_num
        self._annot = annotation
        self._old = old_attrs
        self._new = new_attrs

    @property
    def description(self) -> str:
        return "Move annotation"

    def execute(self):
        for k, v in self._new.items():
            setattr(self._annot, k, v)
        self._doc.modified = True

    def undo(self):
        for k, v in self._old.items():
            setattr(self._annot, k, v)
        self._doc.modified = True


class InsertImageCommand(Command):
    """Insert an image into a PDF page."""

    def __init__(self, pdf_doc, page_num: int, annotation):
        self._doc = pdf_doc
        self._page = page_num
        self._annot = annotation

    @property
    def description(self) -> str:
        return "Insert image"

    def execute(self):
        self._doc.add_pending_annotation(self._page, self._annot)

    def undo(self):
        self._doc.remove_pending_annotation(self._page, self._annot)


class FormFieldEditCommand(Command):
    """Edit a form field value."""

    def __init__(self, pdf_doc, page_num: int, field_xref: int, old_value, new_value):
        self._doc = pdf_doc
        self._page = page_num
        self._xref = field_xref
        self._old = old_value
        self._new = new_value

    @property
    def description(self) -> str:
        return "Edit form field"

    def execute(self):
        page = self._doc.get_page(self._page)
        for widget in page.widgets():
            if widget.xref == self._xref:
                widget.field_value = self._new
                widget.update()
                break
        self._doc.modified = True

    def undo(self):
        page = self._doc.get_page(self._page)
        for widget in page.widgets():
            if widget.xref == self._xref:
                widget.field_value = self._old
                widget.update()
                break
        self._doc.modified = True
