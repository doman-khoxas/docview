"""Export/Save-As dialog with flatten option."""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel,
    QFileDialog, QMessageBox, QDialogButtonBox
)
from PyQt5.QtGui import QFont


class ExportDialog(QDialog):
    def __init__(self, pdf_doc, parent=None):
        super().__init__(parent)
        self._doc = pdf_doc
        self.setWindowTitle("Export PDF")
        self.resize(380, 150)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Export Options"))

        self._flatten_check = QCheckBox("Flatten annotations (burn into page)")
        layout.addWidget(self._flatten_check)

        buttons = QDialogButtonBox()
        export_btn = buttons.addButton("Export", QDialogButtonBox.AcceptRole)
        export_btn.clicked.connect(self._export)
        buttons.addButton(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            self._doc.save_as(path, flatten=self._flatten_check.isChecked())
            QMessageBox.information(self, "Export", f"Exported to:\n{path}")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed:\n{e}")
