"""Dialog for splitting a PDF into parts by page ranges."""
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QFileDialog, QMessageBox, QDialogButtonBox
)
from PyQt5.QtGui import QFont
from app.core.page_operations import split_pdf


class SplitDialog(QDialog):
    def __init__(self, pdf_doc, parent=None):
        super().__init__(parent)
        self._doc = pdf_doc
        self._total = pdf_doc.page_count
        self.setWindowTitle("Split PDF")
        self.resize(400, 250)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Total pages: {self._total}"))
        layout.addWidget(QLabel("Page ranges (e.g. 1-3, 4-6, 7-10):"))

        self._ranges_entry = QLineEdit(f"1-{self._total}")
        layout.addWidget(self._ranges_entry)

        layout.addWidget(QLabel("- OR split every N pages -"))
        every_row = QHBoxLayout()
        every_row.addWidget(QLabel("Every"))
        self._every_entry = QLineEdit()
        self._every_entry.setFixedWidth(60)
        every_row.addWidget(self._every_entry)
        every_row.addWidget(QLabel("pages"))
        every_row.addStretch()
        layout.addLayout(every_row)

        buttons = QDialogButtonBox()
        split_btn = buttons.addButton("Split", QDialogButtonBox.AcceptRole)
        split_btn.clicked.connect(self._split)
        buttons.addButton(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _parse_ranges(self) -> list[tuple[int, int]] | None:
        every_text = self._every_entry.text().strip()
        if every_text:
            try:
                n = int(every_text)
                if n < 1:
                    raise ValueError
                return [(start, min(start + n - 1, self._total - 1))
                        for start in range(0, self._total, n)]
            except ValueError:
                QMessageBox.critical(self, "Error", "Invalid number.")
                return None

        text = self._ranges_entry.text().strip()
        if not text:
            QMessageBox.critical(self, "Error", "Enter page ranges.")
            return None

        ranges = []
        for part in text.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                try:
                    start, end = int(a.strip()) - 1, int(b.strip()) - 1
                    if start < 0 or end >= self._total or start > end:
                        raise ValueError
                    ranges.append((start, end))
                except ValueError:
                    QMessageBox.critical(self, "Error", f"Invalid range: {part}")
                    return None
            else:
                try:
                    p = int(part) - 1
                    if p < 0 or p >= self._total:
                        raise ValueError
                    ranges.append((p, p))
                except ValueError:
                    QMessageBox.critical(self, "Error", f"Invalid page: {part}")
                    return None
        return ranges

    def _split(self):
        ranges = self._parse_ranges()
        if not ranges:
            return
        output_dir = QFileDialog.getExistingDirectory(self, "Select output directory")
        if not output_dir:
            return
        base_name = Path(self._doc.file_path).stem if self._doc.file_path else "split"
        try:
            files = split_pdf(self._doc.doc, ranges, output_dir, base_name)
            QMessageBox.information(self, "Split", f"Created {len(files)} file(s):\n" + "\n".join(files))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Split failed:\n{e}")
