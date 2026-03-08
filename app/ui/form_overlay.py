"""Interactive PDF form filling overlay — renders editable widgets over form fields."""
import tkinter as tk
import fitz
from app.core.pdf_renderer import get_render_scale
from app.config import BG_ABYSS, BORDER_SUBTLE, TEXT_PRIMARY, ACCENT
from app.logger import get_logger

logger = get_logger(__name__)


class FormOverlay:
    """Manages interactive form widgets overlaid on the PDF canvas."""

    def __init__(self, viewport):
        self.viewport = viewport
        self._widgets: list[dict] = []  # [{widget, field, page_num, rect}, ...]
        self._active = False

    @property
    def has_forms(self) -> bool:
        """Check if current document has any form fields."""
        doc = self.viewport.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return False
        for pn in range(doc.page_count):
            page = doc.get_page(pn)
            if any(True for _ in page.widgets()):
                return True
        return False

    def activate(self):
        """Scan all pages for form fields and create overlay widgets."""
        self.deactivate()
        doc = self.viewport.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return

        count = 0
        for pn in range(doc.page_count):
            page = doc.get_page(pn)
            for widget in page.widgets():
                self._create_widget(pn, widget)
                count += 1

        if count > 0:
            self._active = True
            self.update_positions()
            logger.info("Form overlay activated: %d field(s)", count)
        else:
            logger.info("No form fields found in document")

    def deactivate(self):
        """Remove all overlay widgets."""
        for entry in self._widgets:
            w = entry.get("widget")
            if w and w.winfo_exists():
                w.destroy()
        self._widgets.clear()
        self._active = False

    def update_positions(self):
        """Reposition all form widgets based on current scroll/zoom."""
        if not self._active:
            return

        canvas = self.viewport.canvas
        layout = self.viewport._page_layout
        scale = get_render_scale(self.viewport.zoom)
        canvas_w = canvas.winfo_width()

        for entry in self._widgets:
            pn = entry["page_num"]
            rect = entry["rect"]
            w = entry["widget"]

            if pn >= len(layout):
                w.place_forget()
                continue

            y_off, pw, ph = layout[pn]
            x_off = (canvas_w - pw) / 2

            # PDF coords -> canvas coords
            cx = x_off + rect.x0 * scale
            cy = y_off + rect.y0 * scale
            cw = (rect.x1 - rect.x0) * scale
            ch = (rect.y1 - rect.y0) * scale

            # Convert canvas coords to window coords
            wx = cx - float(canvas.canvasx(0))
            wy = cy - float(canvas.canvasy(0))

            # Check if visible
            if wy + ch < 0 or wy > canvas.winfo_height() or wx + cw < 0 or wx > canvas_w:
                w.place_forget()
            else:
                w.place(x=int(wx), y=int(wy), width=max(20, int(cw)), height=max(16, int(ch)))

    def save_values(self):
        """Write filled values back to the PDF form fields."""
        doc = self.viewport.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return 0

        count = 0
        for entry in self._widgets:
            pn = entry["page_num"]
            field = entry["field"]
            field_type = entry["field_type"]

            page = doc.get_page(pn)
            # Find the widget again by name
            for w in page.widgets():
                if w.field_name == field["name"]:
                    if field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                        new_val = entry["widget"].get()
                        if new_val != w.field_value:
                            w.field_value = new_val
                            w.update()
                            count += 1
                    elif field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                        var = entry.get("var")
                        if var:
                            w.field_value = "Yes" if var.get() else "Off"
                            w.update()
                            count += 1
                    elif field_type == fitz.PDF_WIDGET_TYPE_COMBOBOX:
                        var = entry.get("var")
                        if var:
                            w.field_value = var.get()
                            w.update()
                            count += 1
                    break

        if count > 0:
            doc.modified = True
            logger.info("Saved %d form field value(s)", count)
        return count

    def _create_widget(self, page_num: int, widget):
        """Create a tkinter widget for a PDF form field."""
        canvas = self.viewport.canvas
        field_type = widget.field_type
        field_name = widget.field_name or ""
        field_value = widget.field_value or ""
        rect = widget.rect

        field_info = {"name": field_name, "value": field_value}

        if field_type == fitz.PDF_WIDGET_TYPE_TEXT:
            w = tk.Entry(
                canvas, bg="#FFFFFF", fg="#000000",
                font=("Segoe UI", 9),
                relief="solid", bd=1,
                highlightcolor=ACCENT, highlightthickness=1
            )
            w.insert(0, field_value)
            self._widgets.append({
                "widget": w, "field": field_info, "page_num": page_num,
                "rect": rect, "field_type": field_type
            })

        elif field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
            var = tk.BooleanVar(value=(field_value == "Yes"))
            w = tk.Checkbutton(
                canvas, variable=var, bg="#FFFFFF",
                activebackground="#E0E0E0",
                relief="flat", bd=0
            )
            self._widgets.append({
                "widget": w, "field": field_info, "page_num": page_num,
                "rect": rect, "field_type": field_type, "var": var
            })

        elif field_type in (fitz.PDF_WIDGET_TYPE_COMBOBOX, fitz.PDF_WIDGET_TYPE_LISTBOX):
            choices = widget.choice_values or []
            var = tk.StringVar(value=field_value)
            if choices:
                import tkinter.ttk as ttk
                w = ttk.Combobox(canvas, textvariable=var, values=choices,
                                 font=("Segoe UI", 9))
            else:
                w = tk.Entry(
                    canvas, bg="#FFFFFF", fg="#000000",
                    font=("Segoe UI", 9), relief="solid", bd=1
                )
                w.insert(0, field_value)
            self._widgets.append({
                "widget": w, "field": field_info, "page_num": page_num,
                "rect": rect, "field_type": field_type, "var": var
            })
