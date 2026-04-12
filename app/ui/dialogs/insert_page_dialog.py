"""Dialog for inserting pages."""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QRadioButton, QPushButton, QFileDialog, QMessageBox,
    QDialogButtonBox, QButtonGroup
)
from app.core.page_operations import insert_blank_page, insert_pages_from_file


class InsertPageDialog(QDialog):
    def __init__(self, pdf_doc, current_page: int, parent=None):
        super().__init__(parent)
        self._doc = pdf_doc
        self.setWindowTitle("Insert Page")
        self.resize(380, 200)
        self._setup_ui(current_page)

    def _setup_ui(self, current_page):
        layout = QVBoxLayout(self)

        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Insert after page:"))
        self._pos_entry = QLineEdit(str(current_page + 1))
        self._pos_entry.setFixedWidth(60)
        pos_row.addWidget(self._pos_entry)
        pos_row.addStretch()
        layout.addLayout(pos_row)

        self._blank_radio = QRadioButton("Insert blank page")
        self._blank_radio.setChecked(True)
        self._file_radio = QRadioButton("Insert from file")
        group = QButtonGroup(self)
        group.addButton(self._blank_radio)
        group.addButton(self._file_radio)
        layout.addWidget(self._blank_radio)
        layout.addWidget(self._file_radio)

        buttons = QDialogButtonBox()
        insert_btn = buttons.addButton("Insert", QDialogButtonBox.AcceptRole)
        insert_btn.clicked.connect(self._insert)
        buttons.addButton(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        layout.addWidget(buttons)

    def _insert(self):
        try:
            pos = int(self._pos_entry.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid page number.")
            return

        if self._blank_radio.isChecked():
            insert_blank_page(self._doc.doc, pos)
            self._doc.modified = True
            self.accept()
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
            if not path:
                return
            try:
                insert_pages_from_file(self._doc.doc, pos, path)
                self._doc.modified = True
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed:\n{e}")
