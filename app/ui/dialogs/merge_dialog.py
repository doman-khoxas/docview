"""Dialog for merging multiple PDF files."""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLabel, QFileDialog, QMessageBox, QDialogButtonBox
)
from PyQt5.QtGui import QFont
from app.core.page_operations import merge_pdfs


class MergeDialog(QDialog):
    def __init__(self, parent=None, open_callback=None):
        super().__init__(parent)
        self._open_callback = open_callback
        self.setWindowTitle("Merge PDFs")
        self.resize(500, 400)
        self._files: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("Files to merge (in order):")
        label.setFont(QFont("Segoe UI", 11, QFont.DemiBold))
        layout.addWidget(label)

        self._list = QListWidget()
        layout.addWidget(self._list)

        btn_row = QHBoxLayout()
        for text, fn in [("Add Files", self._add_files), ("Move Up", self._move_up),
                         ("Move Down", self._move_down), ("Remove", self._remove)]:
            btn = QPushButton(text)
            btn.clicked.connect(fn)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

        buttons = QDialogButtonBox()
        merge_btn = buttons.addButton("Merge", QDialogButtonBox.AcceptRole)
        merge_btn.clicked.connect(self._merge)
        cancel_btn = buttons.addButton(QDialogButtonBox.Cancel)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh(self):
        self._list.clear()
        self._list.addItems(self._files)

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select PDFs", "", "PDF Files (*.pdf)")
        self._files.extend(paths)
        self._refresh()

    def _move_up(self):
        i = self._list.currentRow()
        if i > 0:
            self._files[i], self._files[i - 1] = self._files[i - 1], self._files[i]
            self._refresh()
            self._list.setCurrentRow(i - 1)

    def _move_down(self):
        i = self._list.currentRow()
        if 0 <= i < len(self._files) - 1:
            self._files[i], self._files[i + 1] = self._files[i + 1], self._files[i]
            self._refresh()
            self._list.setCurrentRow(i + 1)

    def _remove(self):
        i = self._list.currentRow()
        if 0 <= i < len(self._files):
            self._files.pop(i)
            self._refresh()

    def _merge(self):
        if len(self._files) < 2:
            QMessageBox.warning(self, "Merge", "Add at least 2 files to merge.")
            return
        output, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "", "PDF Files (*.pdf)")
        if not output:
            return
        try:
            merge_pdfs(self._files, output)
            QMessageBox.information(self, "Merge", f"Merged PDF saved to:\n{output}")
            if self._open_callback:
                self._open_callback(output)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Merge failed:\n{e}")
