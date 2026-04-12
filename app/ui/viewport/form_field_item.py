"""Interactive QGraphicsItem overlays for PDF form fields."""
from PyQt5.QtWidgets import (
    QGraphicsRectItem, QGraphicsProxyWidget, QLineEdit,
    QCheckBox, QComboBox, QWidget
)
from PyQt5.QtGui import QPen, QColor, QBrush, QFont
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QObject
from app.core.form_fields import FormField
from app.ui.theme import ACCENT, BG_INPUT


class FormFieldSignals(QObject):
    """Signals for form field value changes."""
    value_changed = pyqtSignal(int, int, str, str)  # page, xref, old_value, new_value


class FormFieldOverlay:
    """Manages form field overlay items on a QGraphicsScene."""

    def __init__(self, scene, zoom: float):
        self._scene = scene
        self._zoom = zoom
        self._items: list[QGraphicsRectItem | QGraphicsProxyWidget] = []
        self._proxy_widgets: list[QGraphicsProxyWidget] = []
        self.signals = FormFieldSignals()

    def clear(self):
        for item in self._items:
            if item.scene():
                item.scene().removeItem(item)
        for pw in self._proxy_widgets:
            if pw.scene():
                pw.scene().removeItem(pw)
        self._items.clear()
        self._proxy_widgets.clear()

    def show_fields(self, fields: list[FormField], page_offset_x: float, page_offset_y: float, scale: float):
        """Create overlay items for form fields on a page."""
        for field in fields:
            if field.is_read_only:
                continue

            x0, y0, x1, y1 = field.rect
            sx0 = page_offset_x + x0 * scale
            sy0 = page_offset_y + y0 * scale
            sw = (x1 - x0) * scale
            sh = (y1 - y0) * scale

            if field.field_type == 1:  # Text
                self._add_text_field(field, sx0, sy0, sw, sh)
            elif field.field_type == 2:  # Checkbox
                self._add_checkbox_field(field, sx0, sy0, sw, sh)
            elif field.field_type == 4:  # Combo
                self._add_combo_field(field, sx0, sy0, sw, sh)
            else:
                # Generic highlight for unsupported types
                self._add_highlight(sx0, sy0, sw, sh)

    def _add_text_field(self, field: FormField, x, y, w, h):
        edit = QLineEdit()
        edit.setText(field.field_value)
        edit.setStyleSheet(
            f"background: rgba(255,255,255,0.9); border: 1px solid {ACCENT}; "
            f"padding: 1px; font-size: {max(8, int(h * 0.6))}px;"
        )
        edit.setFixedSize(int(w), int(h))

        old_value = field.field_value

        def on_edit():
            new_val = edit.text()
            if new_val != old_value:
                self.signals.value_changed.emit(
                    field.page_num, field.xref, old_value, new_val)

        edit.editingFinished.connect(on_edit)

        proxy = self._scene.addWidget(edit)
        proxy.setPos(x, y)
        proxy.setZValue(100)
        self._proxy_widgets.append(proxy)

    def _add_checkbox_field(self, field: FormField, x, y, w, h):
        cb = QCheckBox()
        checked = field.field_value.lower() in ("yes", "on", "true", "1")
        cb.setChecked(checked)
        cb.setStyleSheet("background: rgba(255,255,255,0.9);")
        cb.setFixedSize(int(w), int(h))

        old_value = field.field_value

        def on_toggle(state):
            new_val = "Yes" if state else "Off"
            self.signals.value_changed.emit(
                field.page_num, field.xref, old_value, new_val)

        cb.stateChanged.connect(on_toggle)

        proxy = self._scene.addWidget(cb)
        proxy.setPos(x, y)
        proxy.setZValue(100)
        self._proxy_widgets.append(proxy)

    def _add_combo_field(self, field: FormField, x, y, w, h):
        combo = QComboBox()
        if field.options:
            combo.addItems(field.options)
        if field.field_value:
            idx = combo.findText(field.field_value)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.setStyleSheet(f"background: rgba(255,255,255,0.9); border: 1px solid {ACCENT};")
        combo.setFixedSize(int(w), int(h))

        old_value = field.field_value

        def on_change(text):
            self.signals.value_changed.emit(
                field.page_num, field.xref, old_value, text)

        combo.currentTextChanged.connect(on_change)

        proxy = self._scene.addWidget(combo)
        proxy.setPos(x, y)
        proxy.setZValue(100)
        self._proxy_widgets.append(proxy)

    def _add_highlight(self, x, y, w, h):
        rect = QRectF(x, y, w, h)
        pen = QPen(QColor(ACCENT), 1.5)
        brush = QBrush(QColor(0, 122, 204, 25))
        item = self._scene.addRect(rect, pen, brush)
        item.setZValue(50)
        self._items.append(item)
