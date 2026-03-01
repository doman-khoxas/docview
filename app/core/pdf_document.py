"""Wraps pymupdf.Document with pending annotation storage."""
import fitz
from pathlib import Path


class PDFDocument:
    def __init__(self):
        self._doc: fitz.Document | None = None
        self._file_path: str | None = None
        self._pending_annotations: dict[int, list] = {}  # page_num -> [annotations]
        self._modified = False

    @property
    def doc(self) -> fitz.Document | None:
        return self._doc

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
        return self._doc is not None

    @property
    def page_count(self) -> int:
        return self._doc.page_count if self._doc else 0

    @property
    def modified(self) -> bool:
        return self._modified

    @modified.setter
    def modified(self, value: bool):
        self._modified = value

    def open(self, file_path: str):
        self.close()
        self._doc = fitz.open(file_path)
        self._file_path = file_path
        self._pending_annotations.clear()
        self._modified = False

    def close(self):
        if self._doc:
            self._doc.close()
            self._doc = None
        self._file_path = None
        self._pending_annotations.clear()
        self._modified = False

    def get_page(self, page_num: int) -> fitz.Page:
        if not self._doc or page_num < 0 or page_num >= self.page_count:
            raise IndexError(f"Page {page_num} out of range")
        return self._doc[page_num]

    def add_pending_annotation(self, page_num: int, annotation):
        if page_num not in self._pending_annotations:
            self._pending_annotations[page_num] = []
        self._pending_annotations[page_num].append(annotation)
        self._modified = True

    def remove_pending_annotation(self, page_num: int, annotation):
        if page_num in self._pending_annotations:
            try:
                self._pending_annotations[page_num].remove(annotation)
                self._modified = True
            except ValueError:
                pass

    def get_pending_annotations(self, page_num: int) -> list:
        return self._pending_annotations.get(page_num, [])

    def get_all_pending_annotations(self) -> dict[int, list]:
        return self._pending_annotations

    def commit_annotations(self):
        from app.core.annotation_model import commit_to_pdf
        for page_num, annotations in self._pending_annotations.items():
            if annotations:
                page = self.get_page(page_num)
                for annot in annotations:
                    commit_to_pdf(page, annot)
        self._pending_annotations.clear()

    def save(self, file_path: str | None = None):
        if not self._doc:
            return
        self.commit_annotations()
        save_path = file_path or self._file_path
        if save_path == self._file_path:
            try:
                self._doc.saveIncr()
            except Exception:
                self._doc.save(save_path, garbage=4, deflate=True)
        else:
            self._doc.save(save_path)
            self._file_path = save_path
        self._modified = False

    def save_as(self, file_path: str, flatten: bool = False):
        if not self._doc:
            return
        self.commit_annotations()
        if flatten:
            for page_num in range(self.page_count):
                page = self._doc[page_num]
                pix = page.get_pixmap(dpi=300)
                # Remove existing annotations
                while page.annots():
                    annot = page.annots().__next__()
                    page.delete_annot(annot)
                # Burn page content as image
                page.clean_contents()
                img_rect = page.rect
                page.insert_image(img_rect, pixmap=pix)
        self._doc.save(file_path, garbage=4, deflate=True)
        self._file_path = file_path
        self._modified = False

    def new_document(self):
        self.close()
        self._doc = fitz.open()
        self._file_path = None
        self._modified = False
