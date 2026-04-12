"""PDF form field detection and management."""
import fitz
from dataclasses import dataclass


@dataclass
class FormField:
    """Represents a detected PDF form field."""
    page_num: int
    xref: int
    field_type: int      # fitz widget types: 1=Text, 2=Checkbox, 3=Radio, 4=Combo, 5=Listbox, 7=Signature
    field_name: str
    field_value: str
    rect: tuple[float, float, float, float]  # x0, y0, x1, y1 in PDF coords
    options: list[str]   # for combo/listbox
    is_read_only: bool

    @property
    def type_name(self) -> str:
        return {1: "text", 2: "checkbox", 3: "radio", 4: "combo",
                5: "listbox", 7: "signature"}.get(self.field_type, "unknown")


class FormFieldManager:
    """Scans PDF pages for form fields and manages their values."""

    def __init__(self):
        self._fields: dict[int, list[FormField]] = {}  # page_num -> fields

    def scan_document(self, pdf_doc) -> int:
        """Scan all pages for form fields. Returns total field count."""
        self._fields.clear()
        if not pdf_doc or not pdf_doc.is_open:
            return 0

        total = 0
        for page_num in range(pdf_doc.page_count):
            page = pdf_doc.get_page(page_num)
            widgets = list(page.widgets())
            if not widgets:
                continue

            page_fields = []
            for w in widgets:
                field = FormField(
                    page_num=page_num,
                    xref=w.xref,
                    field_type=w.field_type,
                    field_name=w.field_name or "",
                    field_value=w.field_value or "",
                    rect=(w.rect.x0, w.rect.y0, w.rect.x1, w.rect.y1),
                    options=w.choice_values or [] if hasattr(w, 'choice_values') else [],
                    is_read_only=bool(w.field_flags & 1) if w.field_flags else False,
                )
                page_fields.append(field)

            if page_fields:
                self._fields[page_num] = page_fields
                total += len(page_fields)

        return total

    def get_fields(self, page_num: int) -> list[FormField]:
        return self._fields.get(page_num, [])

    def get_all_fields(self) -> dict[int, list[FormField]]:
        return self._fields

    @property
    def has_fields(self) -> bool:
        return bool(self._fields)

    @property
    def total_count(self) -> int:
        return sum(len(fields) for fields in self._fields.values())

    def set_field_value(self, pdf_doc, page_num: int, xref: int, value: str) -> str | None:
        """Set a form field value. Returns the old value or None."""
        page = pdf_doc.get_page(page_num)
        for w in page.widgets():
            if w.xref == xref:
                old = w.field_value
                w.field_value = value
                w.update()
                # Update cached field
                for f in self._fields.get(page_num, []):
                    if f.xref == xref:
                        f.field_value = value
                        break
                pdf_doc.modified = True
                return old
        return None
