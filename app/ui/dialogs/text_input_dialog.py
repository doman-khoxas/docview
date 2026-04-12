"""Simple text input dialog (PyQt5)."""
from PyQt5.QtWidgets import QInputDialog


def get_text_input(parent, title="Enter Text", label="Text:") -> str | None:
    """Show a text input dialog. Returns text or None if cancelled."""
    text, ok = QInputDialog.getMultiLineText(parent, title, label)
    return text if ok and text.strip() else None
