#!/usr/bin/env python3
"""
PDF Paint — A MS Paint-inspired PDF Editor with Redaction & OCR
Windows 7 Ribbon-style toolbar | Full annotation suite | ocrmypdf integration

Usage:
  GUI Mode:   python pdf_paint.py [file.pdf]
  CLI Mode:   python pdf_paint.py --cli --input file.pdf --redact "page:1,x:50,y:100,w:200,h:30" --output redacted.pdf
  OCR Mode:   python pdf_paint.py --cli --input scanned.pdf --ocr --output searchable.pdf
"""

import sys
import os
import subprocess
import json
import argparse
import tempfile
from pathlib import Path

# ── CLI-only imports (always available) ──
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

# ── GUI imports (optional for CLI mode) ──
HAS_GUI = False
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QToolBar, QAction, QActionGroup, QLabel, QPushButton, QComboBox,
        QSpinBox, QColorDialog, QFileDialog, QScrollArea, QStatusBar,
        QMessageBox, QInputDialog, QToolButton, QMenu, QFrame,
        QSizePolicy, QGroupBox, QGridLayout, QSlider, QProgressDialog,
        QDialog, QTextEdit, QDialogButtonBox, QCheckBox
    )
    from PyQt5.QtCore import Qt, QPoint, QRect, QSize, QTimer, pyqtSignal
    from PyQt5.QtGui import (
        QPixmap, QPainter, QPen, QColor, QFont, QIcon, QImage,
        QCursor, QBrush, QPainterPath, QTransform, QPalette
    )
    HAS_GUI = True
except ImportError:
    pass


# ═══════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════
APP_NAME = "PDF Paint"
APP_VERSION = "1.0"
DEFAULT_PEN_WIDTH = 3
DEFAULT_HIGHLIGHT_WIDTH = 20
ZOOM_LEVELS = [25, 50, 75, 100, 125, 150, 200, 300, 400]

# Windows 7 Ribbon Colors
RIBBON_BG = "#F0F0F0"
RIBBON_BORDER = "#B8B8B8"
RIBBON_GROUP_BG = "#FAFAFA"
RIBBON_ACTIVE = "#FED8A0"
RIBBON_HOVER = "#FDE8C8"
RIBBON_TAB_BG = "#4A90D9"
RIBBON_TAB_TEXT = "#FFFFFF"
TOOLBAR_ICON_SIZE = 28

# Tool enum
class Tool:
    SELECT = "select"
    PEN = "pen"
    HIGHLIGHTER = "highlighter"
    ERASER = "eraser"
    TEXT = "text"
    RECT = "rect"
    CIRCLE = "circle"
    LINE = "line"
    ARROW = "arrow"
    REDACT = "redact"


# ═══════════════════════════════════════════════════
# CLI ENGINE — Works without GUI for Claude Code
# ═══════════════════════════════════════════════════
class PDFEngine:
    """Core PDF operations — no GUI dependency."""

    def __init__(self, filepath=None):
        if not HAS_FITZ:
            raise ImportError("PyMuPDF (fitz) required. Install: pip install PyMuPDF")
        self.doc = None
        self.filepath = filepath
        self.annotations = {}  # page_num -> list of annotation dicts
        if filepath:
            self.load(filepath)

    def load(self, filepath):
        self.filepath = filepath
        self.doc = fitz.open(filepath)
        return self

    def page_count(self):
        return len(self.doc) if self.doc else 0

    def get_page_pixmap(self, page_num, zoom=1.0):
        """Render page to pixmap."""
        page = self.doc[page_num]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix

    def redact_area(self, page_num, x, y, w, h):
        """Apply redaction to a rectangular area on a page."""
        page = self.doc[page_num]
        rect = fitz.Rect(x, y, x + w, y + h)
        page.add_redact_annot(rect, fill=(0, 0, 0))
        page.apply_redactions()
        return True

    def redact_text(self, page_num, search_text):
        """Redact all occurrences of text on a page."""
        page = self.doc[page_num]
        text_instances = page.search_for(search_text)
        for inst in text_instances:
            page.add_redact_annot(inst, fill=(0, 0, 0))
        page.apply_redactions()
        return len(text_instances)

    def add_text_annotation(self, page_num, x, y, text, fontsize=12, color=(0, 0, 0)):
        """Add text to a page."""
        page = self.doc[page_num]
        point = fitz.Point(x, y)
        rc = page.insert_text(point, text, fontsize=fontsize, color=color)
        return rc

    def draw_rect_annotation(self, page_num, x, y, w, h, color=(1, 0, 0), width=2, fill=None):
        """Draw rectangle on page."""
        page = self.doc[page_num]
        rect = fitz.Rect(x, y, x + w, y + h)
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=color, width=width, fill=fill)
        shape.commit()

    def draw_line_annotation(self, page_num, x1, y1, x2, y2, color=(0, 0, 0), width=2):
        """Draw line on page."""
        page = self.doc[page_num]
        shape = page.new_shape()
        shape.draw_line(fitz.Point(x1, y1), fitz.Point(x2, y2))
        shape.finish(color=color, width=width)
        shape.commit()

    def draw_circle_annotation(self, page_num, cx, cy, r, color=(0, 0, 1), width=2, fill=None):
        """Draw circle/oval on page."""
        page = self.doc[page_num]
        rect = fitz.Rect(cx - r, cy - r, cx + r, cy + r)
        shape = page.new_shape()
        shape.draw_oval(rect)
        shape.finish(color=color, width=width, fill=fill)
        shape.commit()

    def highlight_area(self, page_num, x, y, w, h, color=(1, 1, 0)):
        """Add semi-transparent highlight."""
        page = self.doc[page_num]
        rect = fitz.Rect(x, y, x + w, y + h)
        annot = page.add_highlight_annot(rect)
        annot.set_colors(stroke=color)
        annot.update()

    def ocr_document(self, output_path=None, language="eng", deskew=True, force=False):
        """Run OCR using ocrmypdf."""
        if not output_path:
            base, ext = os.path.splitext(self.filepath)
            output_path = f"{base}_ocr{ext}"

        # Save current state to temp file first
        temp_input = tempfile.mktemp(suffix=".pdf")
        self.doc.save(temp_input)

        cmd = ["ocrmypdf"]
        if language:
            cmd.extend(["-l", language])
        if deskew:
            cmd.append("--deskew")
        if force:
            cmd.append("--force-ocr")
        cmd.extend(["--skip-text", temp_input, output_path])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            os.unlink(temp_input)
            if result.returncode == 0:
                return output_path
            elif result.returncode == 6:
                # Already has text, try without --skip-text
                cmd_retry = ["ocrmypdf"]
                if language:
                    cmd_retry.extend(["-l", language])
                if deskew:
                    cmd_retry.append("--deskew")
                cmd_retry.append("--force-ocr")
                temp_input2 = tempfile.mktemp(suffix=".pdf")
                self.doc.save(temp_input2)
                cmd_retry.extend([temp_input2, output_path])
                result2 = subprocess.run(cmd_retry, capture_output=True, text=True, timeout=300)
                os.unlink(temp_input2)
                if result2.returncode == 0:
                    return output_path
                else:
                    raise RuntimeError(f"OCR failed: {result2.stderr}")
            else:
                raise RuntimeError(f"OCR failed: {result.stderr}")
        except FileNotFoundError:
            raise RuntimeError("ocrmypdf not found. Install: pip install ocrmypdf")

    def save(self, output_path=None):
        """Save the PDF."""
        if not output_path:
            output_path = self.filepath
        if output_path == self.filepath:
            self.doc.saveIncr()
        else:
            self.doc.save(output_path)
        return output_path

    def save_as(self, output_path):
        self.doc.save(output_path)
        self.filepath = output_path
        return output_path

    def close(self):
        if self.doc:
            self.doc.close()

    def get_text(self, page_num):
        """Extract text from page."""
        page = self.doc[page_num]
        return page.get_text()

    def get_all_text(self):
        """Extract text from all pages."""
        texts = []
        for i in range(len(self.doc)):
            texts.append(f"--- Page {i+1} ---\n{self.get_text(i)}")
        return "\n\n".join(texts)


# ═══════════════════════════════════════════════════
# GUI — PDF Canvas Widget
# ═══════════════════════════════════════════════════
if HAS_GUI:

    class PDFCanvas(QLabel):
        """Canvas widget for PDF page display and annotation drawing."""
        zoom_changed = pyqtSignal(float)

        def __init__(self, parent=None):
            super().__init__(parent)
            self.engine = None
            self.current_page = 0
            self.zoom = 1.0
            self.tool = Tool.SELECT
            self.pen_color = QColor(0, 0, 0)
            self.pen_width = DEFAULT_PEN_WIDTH
            self.highlight_color = QColor(255, 255, 0, 100)

            # Drawing state
            self.drawing = False
            self.last_point = QPoint()
            self.start_point = QPoint()
            self.temp_pixmap = None  # For shape preview
            self.overlay_pixmap = None  # Persistent annotations layer
            self.base_pixmap = None  # PDF page render

            # Redaction state
            self.redact_rects = []  # List of QRect for pending redactions
            self.redact_preview = None  # Current drag rect

            # Text tool
            self.text_font = QFont("Arial", 14)

            self.setAlignment(Qt.AlignCenter)
            self.setMouseTracking(True)
            self.setCursor(Qt.CrossCursor)

        def set_engine(self, engine):
            self.engine = engine
            self.current_page = 0
            self.redact_rects = []
            self.render_page()

        def render_page(self):
            """Render current page from PDF."""
            if not self.engine or self.engine.page_count() == 0:
                return

            pix = self.engine.get_page_pixmap(self.current_page, self.zoom)
            img_data = pix.samples
            qimg = QImage(img_data, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            self.base_pixmap = QPixmap.fromImage(qimg)
            self.overlay_pixmap = QPixmap(self.base_pixmap.size())
            self.overlay_pixmap.fill(Qt.transparent)
            self._compose_display()

        def _compose_display(self):
            """Compose base + overlay + redaction preview for display."""
            if not self.base_pixmap:
                return
            display = QPixmap(self.base_pixmap)
            painter = QPainter(display)

            # Draw overlay annotations
            if self.overlay_pixmap:
                painter.drawPixmap(0, 0, self.overlay_pixmap)

            # Draw pending redaction boxes (red outline preview)
            painter.setPen(QPen(QColor(255, 0, 0), 2, Qt.DashLine))
            painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
            for rect in self.redact_rects:
                painter.drawRect(rect)

            # Draw active redaction drag
            if self.redact_preview:
                painter.setPen(QPen(QColor(255, 0, 0, 200), 2, Qt.DashLine))
                painter.setBrush(QBrush(QColor(255, 0, 0, 50)))
                painter.drawRect(self.redact_preview)

            painter.end()
            self.setPixmap(display)
            self.setMinimumSize(display.size())

        def set_page(self, page_num):
            if self.engine and 0 <= page_num < self.engine.page_count():
                self.current_page = page_num
                self.redact_rects = []
                self.render_page()

        def set_zoom(self, zoom):
            self.zoom = zoom
            self.render_page()
            self.zoom_changed.emit(zoom)

        # ── Mouse Events ──
        def mousePressEvent(self, event):
            if event.button() != Qt.LeftButton or not self.base_pixmap:
                return

            pos = event.pos()
            self.drawing = True
            self.start_point = pos
            self.last_point = pos

            if self.tool == Tool.REDACT:
                self.redact_preview = QRect(pos, QSize(0, 0))

            elif self.tool in (Tool.PEN, Tool.HIGHLIGHTER, Tool.ERASER):
                pass  # Will draw in mouseMoveEvent

            elif self.tool == Tool.TEXT:
                self._place_text(pos)
                self.drawing = False

        def mouseMoveEvent(self, event):
            if not self.drawing or not self.overlay_pixmap:
                return

            pos = event.pos()

            if self.tool == Tool.PEN:
                painter = QPainter(self.overlay_pixmap)
                pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(self.last_point, pos)
                painter.end()
                self.last_point = pos
                self._compose_display()

            elif self.tool == Tool.HIGHLIGHTER:
                painter = QPainter(self.overlay_pixmap)
                color = QColor(self.highlight_color)
                color.setAlpha(30)
                pen = QPen(color, DEFAULT_HIGHLIGHT_WIDTH, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.setPen(pen)
                painter.drawLine(self.last_point, pos)
                painter.end()
                self.last_point = pos
                self._compose_display()

            elif self.tool == Tool.ERASER:
                painter = QPainter(self.overlay_pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                pen = QPen(Qt.transparent, self.pen_width * 3, Qt.SolidLine, Qt.RoundCap)
                painter.setPen(pen)
                painter.drawLine(self.last_point, pos)
                painter.end()
                self.last_point = pos
                self._compose_display()

            elif self.tool == Tool.REDACT:
                self.redact_preview = QRect(self.start_point, pos).normalized()
                self._compose_display()

            elif self.tool in (Tool.RECT, Tool.CIRCLE, Tool.LINE, Tool.ARROW):
                # Preview shape on temp display
                self._compose_display()
                display = self.pixmap()
                painter = QPainter(display)
                pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                r = QRect(self.start_point, pos).normalized()
                if self.tool == Tool.RECT:
                    painter.drawRect(r)
                elif self.tool == Tool.CIRCLE:
                    painter.drawEllipse(r)
                elif self.tool == Tool.LINE:
                    painter.drawLine(self.start_point, pos)
                elif self.tool == Tool.ARROW:
                    painter.drawLine(self.start_point, pos)
                    # Arrowhead
                    self._draw_arrowhead(painter, self.start_point, pos)
                painter.end()
                self.setPixmap(display)

        def mouseReleaseEvent(self, event):
            if event.button() != Qt.LeftButton or not self.drawing:
                return

            pos = event.pos()
            self.drawing = False

            if self.tool == Tool.REDACT and self.redact_preview:
                if self.redact_preview.width() > 5 and self.redact_preview.height() > 5:
                    self.redact_rects.append(self.redact_preview)
                self.redact_preview = None
                self._compose_display()

            elif self.tool in (Tool.RECT, Tool.CIRCLE, Tool.LINE, Tool.ARROW):
                # Commit shape to overlay
                painter = QPainter(self.overlay_pixmap)
                pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                r = QRect(self.start_point, pos).normalized()
                if self.tool == Tool.RECT:
                    painter.drawRect(r)
                elif self.tool == Tool.CIRCLE:
                    painter.drawEllipse(r)
                elif self.tool == Tool.LINE:
                    painter.drawLine(self.start_point, pos)
                elif self.tool == Tool.ARROW:
                    painter.drawLine(self.start_point, pos)
                    self._draw_arrowhead(painter, self.start_point, pos)
                painter.end()
                self._compose_display()

        def _draw_arrowhead(self, painter, start, end):
            """Draw arrowhead at end of line."""
            import math
            dx = end.x() - start.x()
            dy = end.y() - start.y()
            angle = math.atan2(dy, dx)
            arrow_len = 15
            a1 = angle + math.radians(150)
            a2 = angle - math.radians(150)
            p1 = QPoint(int(end.x() + arrow_len * math.cos(a1)),
                        int(end.y() + arrow_len * math.sin(a1)))
            p2 = QPoint(int(end.x() + arrow_len * math.cos(a2)),
                        int(end.y() + arrow_len * math.sin(a2)))
            painter.drawLine(end, p1)
            painter.drawLine(end, p2)

        def _place_text(self, pos):
            """Open text input dialog and place text."""
            text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
            if ok and text:
                painter = QPainter(self.overlay_pixmap)
                painter.setFont(self.text_font)
                painter.setPen(QPen(self.pen_color))
                painter.drawText(pos, text)
                painter.end()
                self._compose_display()

        def apply_redactions(self):
            """Apply all pending redactions to the PDF permanently."""
            if not self.redact_rects or not self.engine:
                return 0

            count = 0
            for rect in self.redact_rects:
                # Convert canvas coords to PDF coords
                x = rect.x() / self.zoom
                y = rect.y() / self.zoom
                w = rect.width() / self.zoom
                h = rect.height() / self.zoom
                self.engine.redact_area(self.current_page, x, y, w, h)
                count += 1

            self.redact_rects = []
            self.render_page()
            return count

        def clear_redactions(self):
            """Clear pending (unapplied) redactions."""
            self.redact_rects = []
            self.redact_preview = None
            self._compose_display()

        def clear_annotations(self):
            """Clear the overlay (drawn annotations)."""
            if self.overlay_pixmap:
                self.overlay_pixmap.fill(Qt.transparent)
                self._compose_display()


    # ═══════════════════════════════════════════════════
    # RIBBON TOOLBAR — Windows 7 Paint Style
    # ═══════════════════════════════════════════════════
    class RibbonGroup(QGroupBox):
        """A grouped section in the ribbon toolbar."""
        def __init__(self, title, parent=None):
            super().__init__(title, parent)
            self.setStyleSheet(f"""
                QGroupBox {{
                    background: {RIBBON_GROUP_BG};
                    border: 1px solid {RIBBON_BORDER};
                    border-radius: 3px;
                    margin-top: 8px;
                    padding: 4px;
                    padding-top: 14px;
                    font-size: 9px;
                    color: #555;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: bottom center;
                    padding: 0 4px;
                    background: {RIBBON_GROUP_BG};
                    font-weight: bold;
                }}
            """)
            self.layout = QHBoxLayout()
            self.layout.setSpacing(2)
            self.layout.setContentsMargins(4, 2, 4, 2)
            self.setLayout(self.layout)

        def add_widget(self, widget):
            self.layout.addWidget(widget)


    class ToolButton(QPushButton):
        """A ribbon-style tool button."""
        def __init__(self, text, icon_char="", tooltip="", parent=None):
            super().__init__(parent)
            display_text = f"{icon_char}\n{text}" if icon_char else text
            self.setText(display_text)
            self.setToolTip(tooltip or text)
            self.setCheckable(True)
            self.setFixedSize(52, 52)
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 3px;
                    font-size: 9px;
                    padding: 2px;
                }}
                QPushButton:hover {{
                    background: {RIBBON_HOVER};
                    border: 1px solid #E0C080;
                }}
                QPushButton:checked {{
                    background: {RIBBON_ACTIVE};
                    border: 1px solid #D0A030;
                }}
            """)


    class ActionButton(QPushButton):
        """A ribbon-style action button (non-checkable)."""
        def __init__(self, text, icon_char="", tooltip="", parent=None):
            super().__init__(parent)
            display_text = f"{icon_char}\n{text}" if icon_char else text
            self.setText(display_text)
            self.setToolTip(tooltip or text)
            self.setFixedSize(52, 52)
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 3px;
                    font-size: 9px;
                    padding: 2px;
                }}
                QPushButton:hover {{
                    background: {RIBBON_HOVER};
                    border: 1px solid #E0C080;
                }}
                QPushButton:pressed {{
                    background: {RIBBON_ACTIVE};
                    border: 1px solid #D0A030;
                }}
            """)


    # ═══════════════════════════════════════════════════
    # MAIN WINDOW
    # ═══════════════════════════════════════════════════
    class PDFPaintWindow(QMainWindow):
        def __init__(self, filepath=None):
            super().__init__()
            self.engine = PDFEngine()
            self.current_file = filepath
            self.tool_buttons = {}

            self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
            self.setMinimumSize(1100, 750)
            self.setStyleSheet(f"""
                QMainWindow {{
                    background: #E8E8E8;
                }}
                QStatusBar {{
                    background: {RIBBON_TAB_BG};
                    color: white;
                    font-size: 11px;
                }}
            """)

            self._build_ui()

            if filepath and os.path.exists(filepath):
                self._open_file(filepath)

        def _build_ui(self):
            # Central widget
            central = QWidget()
            self.setCentralWidget(central)
            main_layout = QVBoxLayout(central)
            main_layout.setSpacing(0)
            main_layout.setContentsMargins(0, 0, 0, 0)

            # ── Ribbon Tab Bar ──
            tab_bar = QFrame()
            tab_bar.setFixedHeight(28)
            tab_bar.setStyleSheet(f"""
                QFrame {{
                    background: {RIBBON_TAB_BG};
                    border: none;
                }}
            """)
            tab_layout = QHBoxLayout(tab_bar)
            tab_layout.setContentsMargins(8, 2, 8, 2)

            title_label = QLabel(f"  {APP_NAME}")
            title_label.setStyleSheet(f"color: {RIBBON_TAB_TEXT}; font-weight: bold; font-size: 13px;")
            tab_layout.addWidget(title_label)

            for tab_name in ["Home", "View", "Redact", "OCR"]:
                btn = QPushButton(tab_name)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {RIBBON_TAB_TEXT};
                        border: none;
                        padding: 2px 12px;
                        font-size: 11px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background: rgba(255,255,255,0.2);
                        border-radius: 2px;
                    }}
                """)
                tab_layout.addWidget(btn)

            tab_layout.addStretch()
            main_layout.addWidget(tab_bar)

            # ── Ribbon Toolbar ──
            ribbon = QFrame()
            ribbon.setFixedHeight(80)
            ribbon.setStyleSheet(f"""
                QFrame {{
                    background: {RIBBON_BG};
                    border-bottom: 1px solid {RIBBON_BORDER};
                }}
            """)
            ribbon_layout = QHBoxLayout(ribbon)
            ribbon_layout.setContentsMargins(6, 2, 6, 2)
            ribbon_layout.setSpacing(6)

            # ── File Group ──
            file_group = RibbonGroup("File")
            btn_open = ActionButton("Open", "\U0001F4C2", "Open PDF (Ctrl+O)")
            btn_open.clicked.connect(self._on_open)
            file_group.add_widget(btn_open)

            btn_save = ActionButton("Save", "\U0001F4BE", "Save PDF (Ctrl+S)")
            btn_save.clicked.connect(self._on_save)
            file_group.add_widget(btn_save)

            btn_saveas = ActionButton("Save As", "\U0001F4CB", "Save As... (Ctrl+Shift+S)")
            btn_saveas.clicked.connect(self._on_save_as)
            file_group.add_widget(btn_saveas)

            ribbon_layout.addWidget(file_group)

            # ── Tools Group ──
            tools_group = RibbonGroup("Tools")
            self.tool_button_group = []

            tool_defs = [
                (Tool.SELECT, "Select", "\u2B9C", "Select / Move"),
                (Tool.PEN, "Pen", "\u270F", "Freehand Pen"),
                (Tool.HIGHLIGHTER, "Highlight", "\U0001F58D", "Highlighter"),
                (Tool.ERASER, "Eraser", "\u2395", "Eraser"),
                (Tool.TEXT, "Text", "A", "Add Text"),
            ]

            for tool_id, name, icon, tooltip in tool_defs:
                btn = ToolButton(name, icon, tooltip)
                btn.clicked.connect(lambda checked, t=tool_id: self._set_tool(t))
                tools_group.add_widget(btn)
                self.tool_buttons[tool_id] = btn
                self.tool_button_group.append(btn)

            ribbon_layout.addWidget(tools_group)

            # ── Shapes Group ──
            shapes_group = RibbonGroup("Shapes")
            shape_defs = [
                (Tool.RECT, "Rect", "\u25AD", "Rectangle"),
                (Tool.CIRCLE, "Circle", "\u25CB", "Circle / Oval"),
                (Tool.LINE, "Line", "\u2571", "Straight Line"),
                (Tool.ARROW, "Arrow", "\u2794", "Arrow"),
            ]

            for tool_id, name, icon, tooltip in shape_defs:
                btn = ToolButton(name, icon, tooltip)
                btn.clicked.connect(lambda checked, t=tool_id: self._set_tool(t))
                shapes_group.add_widget(btn)
                self.tool_buttons[tool_id] = btn
                self.tool_button_group.append(btn)

            ribbon_layout.addWidget(shapes_group)

            # ── Redaction Group ──
            redact_group = RibbonGroup("Redaction")

            btn_redact = ToolButton("Redact", "\u2588", "Redact Area (draw rectangle)")
            btn_redact.setStyleSheet(btn_redact.styleSheet() + """
                QPushButton:checked {
                    background: #FFB0B0;
                    border: 2px solid #CC0000;
                }
            """)
            btn_redact.clicked.connect(lambda: self._set_tool(Tool.REDACT))
            self.tool_buttons[Tool.REDACT] = btn_redact
            self.tool_button_group.append(btn_redact)
            redact_group.add_widget(btn_redact)

            btn_apply_redact = ActionButton("Apply", "\u2714", "Apply all redactions permanently")
            btn_apply_redact.setStyleSheet(btn_apply_redact.styleSheet() + """
                QPushButton { color: #CC0000; font-weight: bold; }
            """)
            btn_apply_redact.clicked.connect(self._on_apply_redactions)
            redact_group.add_widget(btn_apply_redact)

            btn_clear_redact = ActionButton("Clear", "\u2716", "Clear pending redactions")
            btn_clear_redact.clicked.connect(self._on_clear_redactions)
            redact_group.add_widget(btn_clear_redact)

            btn_redact_text = ActionButton("By Text", "\U0001F50D", "Redact by text search")
            btn_redact_text.clicked.connect(self._on_redact_by_text)
            redact_group.add_widget(btn_redact_text)

            ribbon_layout.addWidget(redact_group)

            # ── OCR Group ──
            ocr_group = RibbonGroup("OCR")

            btn_ocr = ActionButton("Run OCR", "\U0001F4D6", "Run OCR on document (ocrmypdf)")
            btn_ocr.clicked.connect(self._on_run_ocr)
            ocr_group.add_widget(btn_ocr)

            btn_extract = ActionButton("Extract", "\U0001F4DD", "Extract text from page")
            btn_extract.clicked.connect(self._on_extract_text)
            ocr_group.add_widget(btn_extract)

            ribbon_layout.addWidget(ocr_group)

            # ── Color & Size Group ──
            color_group = RibbonGroup("Color & Size")

            self.color_btn = ActionButton("Color", "\U0001F3A8", "Pick color")
            self.color_btn.clicked.connect(self._on_pick_color)
            color_group.add_widget(self.color_btn)

            # Pen size
            size_widget = QWidget()
            size_layout = QVBoxLayout(size_widget)
            size_layout.setContentsMargins(0, 0, 0, 0)
            size_layout.setSpacing(1)
            size_label = QLabel("Size:")
            size_label.setStyleSheet("font-size: 9px; color: #555;")
            size_label.setAlignment(Qt.AlignCenter)
            self.size_spin = QSpinBox()
            self.size_spin.setRange(1, 50)
            self.size_spin.setValue(DEFAULT_PEN_WIDTH)
            self.size_spin.setFixedWidth(50)
            self.size_spin.valueChanged.connect(self._on_size_changed)
            size_layout.addWidget(size_label)
            size_layout.addWidget(self.size_spin)
            color_group.add_widget(size_widget)

            ribbon_layout.addWidget(color_group)

            # ── Zoom Group ──
            zoom_group = RibbonGroup("Zoom")
            btn_zin = ActionButton("Zoom+", "+", "Zoom In")
            btn_zin.clicked.connect(lambda: self._on_zoom(1))
            zoom_group.add_widget(btn_zin)

            btn_zout = ActionButton("Zoom-", "-", "Zoom Out")
            btn_zout.clicked.connect(lambda: self._on_zoom(-1))
            zoom_group.add_widget(btn_zout)

            self.zoom_label = QLabel("100%")
            self.zoom_label.setStyleSheet("font-size: 11px; font-weight: bold; min-width: 40px;")
            self.zoom_label.setAlignment(Qt.AlignCenter)
            zoom_group.add_widget(self.zoom_label)

            ribbon_layout.addWidget(zoom_group)

            ribbon_layout.addStretch()
            main_layout.addWidget(ribbon)

            # ── Canvas Area ──
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("""
                QScrollArea {
                    background: #808080;
                    border: none;
                }
            """)

            self.canvas = PDFCanvas()
            scroll.setWidget(self.canvas)
            main_layout.addWidget(scroll, 1)

            # ── Page Navigation Bar ──
            nav_bar = QFrame()
            nav_bar.setFixedHeight(36)
            nav_bar.setStyleSheet(f"""
                QFrame {{
                    background: {RIBBON_BG};
                    border-top: 1px solid {RIBBON_BORDER};
                }}
            """)
            nav_layout = QHBoxLayout(nav_bar)
            nav_layout.setContentsMargins(10, 2, 10, 2)

            btn_prev = QPushButton("\u25C0 Prev")
            btn_prev.clicked.connect(lambda: self._change_page(-1))
            btn_prev.setStyleSheet("padding: 2px 10px;")
            nav_layout.addWidget(btn_prev)

            self.page_label = QLabel("Page 0 / 0")
            self.page_label.setAlignment(Qt.AlignCenter)
            self.page_label.setStyleSheet("font-weight: bold; font-size: 11px;")
            nav_layout.addWidget(self.page_label)

            btn_next = QPushButton("Next \u25B6")
            btn_next.clicked.connect(lambda: self._change_page(1))
            btn_next.setStyleSheet("padding: 2px 10px;")
            nav_layout.addWidget(btn_next)

            nav_layout.addStretch()

            self.file_label = QLabel("No file loaded")
            self.file_label.setStyleSheet("color: #666; font-size: 10px;")
            nav_layout.addWidget(self.file_label)

            main_layout.addWidget(nav_bar)

            # Status bar
            self.statusBar().showMessage(f"{APP_NAME} v{APP_VERSION} — Ready")

            # Set initial tool
            self._set_tool(Tool.SELECT)

            # Keyboard shortcuts
            self._setup_shortcuts()

        def _setup_shortcuts(self):
            from PyQt5.QtWidgets import QShortcut
            from PyQt5.QtGui import QKeySequence
            QShortcut(QKeySequence("Ctrl+O"), self, self._on_open)
            QShortcut(QKeySequence("Ctrl+S"), self, self._on_save)
            QShortcut(QKeySequence("Ctrl+Shift+S"), self, self._on_save_as)
            QShortcut(QKeySequence("Ctrl+Z"), self, self._on_undo)
            QShortcut(QKeySequence("Ctrl++"), self, lambda: self._on_zoom(1))
            QShortcut(QKeySequence("Ctrl+-"), self, lambda: self._on_zoom(-1))

        # ── Tool Selection ──
        def _set_tool(self, tool):
            self.canvas.tool = tool
            for tid, btn in self.tool_buttons.items():
                btn.setChecked(tid == tool)

            # Update cursor
            cursors = {
                Tool.SELECT: Qt.ArrowCursor,
                Tool.PEN: Qt.CrossCursor,
                Tool.HIGHLIGHTER: Qt.CrossCursor,
                Tool.ERASER: Qt.PointingHandCursor,
                Tool.TEXT: Qt.IBeamCursor,
                Tool.RECT: Qt.CrossCursor,
                Tool.CIRCLE: Qt.CrossCursor,
                Tool.LINE: Qt.CrossCursor,
                Tool.ARROW: Qt.CrossCursor,
                Tool.REDACT: Qt.CrossCursor,
            }
            self.canvas.setCursor(cursors.get(tool, Qt.ArrowCursor))
            self.statusBar().showMessage(f"Tool: {tool.upper()}")

        # ── File Operations ──
        def _on_open(self):
            path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
            if path:
                self._open_file(path)

        def _open_file(self, path):
            try:
                self.engine.load(path)
                self.current_file = path
                self.canvas.set_engine(self.engine)
                self._update_page_label()
                self.file_label.setText(os.path.basename(path))
                self.statusBar().showMessage(f"Loaded: {path} ({self.engine.page_count()} pages)")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open PDF:\n{e}")

        def _on_save(self):
            if not self.engine.doc:
                return
            try:
                # Apply any overlay annotations to PDF before saving
                self.canvas.apply_redactions()
                self.engine.save()
                self.statusBar().showMessage(f"Saved: {self.current_file}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

        def _on_save_as(self):
            if not self.engine.doc:
                return
            path, _ = QFileDialog.getSaveFileName(self, "Save PDF As", "", "PDF Files (*.pdf)")
            if path:
                try:
                    self.canvas.apply_redactions()
                    self.engine.save_as(path)
                    self.current_file = path
                    self.file_label.setText(os.path.basename(path))
                    self.statusBar().showMessage(f"Saved as: {path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

        # ── Page Navigation ──
        def _change_page(self, delta):
            new_page = self.canvas.current_page + delta
            if self.engine.doc and 0 <= new_page < self.engine.page_count():
                self.canvas.set_page(new_page)
                self._update_page_label()

        def _update_page_label(self):
            total = self.engine.page_count()
            current = self.canvas.current_page + 1
            self.page_label.setText(f"Page {current} / {total}")

        # ── Zoom ──
        def _on_zoom(self, direction):
            current_idx = 0
            for i, z in enumerate(ZOOM_LEVELS):
                if z / 100.0 >= self.canvas.zoom:
                    current_idx = i
                    break
            new_idx = max(0, min(len(ZOOM_LEVELS) - 1, current_idx + direction))
            new_zoom = ZOOM_LEVELS[new_idx] / 100.0
            self.canvas.set_zoom(new_zoom)
            self.zoom_label.setText(f"{int(new_zoom * 100)}%")

        # ── Color ──
        def _on_pick_color(self):
            color = QColorDialog.getColor(self.canvas.pen_color, self, "Pick Color")
            if color.isValid():
                self.canvas.pen_color = color
                self.canvas.highlight_color = QColor(color.red(), color.green(), color.blue(), 100)

        def _on_size_changed(self, val):
            self.canvas.pen_width = val

        # ── Redaction ──
        def _on_apply_redactions(self):
            if not self.engine.doc:
                return
            count = self.canvas.apply_redactions()
            if count > 0:
                QMessageBox.information(self, "Redaction Applied",
                    f"Applied {count} redaction(s) permanently.\nRemember to save the file.")
                self.statusBar().showMessage(f"Applied {count} redaction(s)")
            else:
                QMessageBox.information(self, "No Redactions", "No pending redactions to apply.")

        def _on_clear_redactions(self):
            self.canvas.clear_redactions()
            self.statusBar().showMessage("Pending redactions cleared")

        def _on_redact_by_text(self):
            if not self.engine.doc:
                return
            text, ok = QInputDialog.getText(self, "Redact by Text",
                "Enter text to redact (all occurrences on current page):")
            if ok and text:
                count = self.engine.redact_text(self.canvas.current_page, text)
                self.canvas.render_page()
                QMessageBox.information(self, "Text Redaction",
                    f"Redacted {count} occurrence(s) of '{text}'")

        # ── OCR ──
        def _on_run_ocr(self):
            if not self.engine.doc or not self.current_file:
                QMessageBox.warning(self, "No File", "Open a PDF first.")
                return

            # Ask for output path
            default_out = self.current_file.replace(".pdf", "_ocr.pdf")
            path, _ = QFileDialog.getSaveFileName(self, "Save OCR Output", default_out, "PDF Files (*.pdf)")
            if not path:
                return

            self.statusBar().showMessage("Running OCR... This may take a minute.")
            QApplication.processEvents()

            try:
                result = self.engine.ocr_document(path)
                QMessageBox.information(self, "OCR Complete", f"OCR output saved to:\n{result}")
                self.statusBar().showMessage(f"OCR complete: {result}")
            except Exception as e:
                QMessageBox.critical(self, "OCR Error", str(e))
                self.statusBar().showMessage("OCR failed")

        def _on_extract_text(self):
            if not self.engine.doc:
                return
            text = self.engine.get_text(self.canvas.current_page)
            dlg = QDialog(self)
            dlg.setWindowTitle(f"Extracted Text — Page {self.canvas.current_page + 1}")
            dlg.resize(600, 400)
            layout = QVBoxLayout(dlg)
            te = QTextEdit()
            te.setPlainText(text if text.strip() else "(No text found — try running OCR first)")
            te.setReadOnly(True)
            layout.addWidget(te)
            bb = QDialogButtonBox(QDialogButtonBox.Ok)
            bb.accepted.connect(dlg.accept)
            layout.addWidget(bb)
            dlg.exec_()

        # ── Undo (clear annotations) ──
        def _on_undo(self):
            self.canvas.clear_annotations()
            self.statusBar().showMessage("Annotations cleared")


# ═══════════════════════════════════════════════════
# CLI MODE — For Claude Code & headless operation
# ═══════════════════════════════════════════════════
def run_cli(args):
    """CLI mode for headless PDF operations."""
    if not HAS_FITZ:
        print("ERROR: PyMuPDF required. Run: pip install PyMuPDF")
        sys.exit(1)

    engine = PDFEngine(args.input)
    print(f"Loaded: {args.input} ({engine.page_count()} pages)")

    # Redaction
    if args.redact:
        for spec in args.redact:
            parts = dict(item.split(":") for item in spec.split(","))
            page = int(parts.get("page", 1)) - 1
            x = float(parts.get("x", 0))
            y = float(parts.get("y", 0))
            w = float(parts.get("w", 100))
            h = float(parts.get("h", 20))
            engine.redact_area(page, x, y, w, h)
            print(f"  Redacted area on page {page+1}: ({x},{y}) {w}x{h}")

    if args.redact_text:
        for spec in args.redact_text:
            parts = spec.split(":", 1)
            if len(parts) == 2:
                page = int(parts[0]) - 1
                text = parts[1]
            else:
                # Apply to all pages
                text = parts[0]
                for p in range(engine.page_count()):
                    count = engine.redact_text(p, text)
                    if count:
                        print(f"  Redacted '{text}' on page {p+1}: {count} occurrences")
                text = None  # Already handled
            if text:
                count = engine.redact_text(page, text)
                print(f"  Redacted '{text}' on page {page+1}: {count} occurrences")

    # OCR
    if args.ocr:
        print("Running OCR...")
        try:
            result = engine.ocr_document(
                args.output,
                language=args.lang or "eng",
                deskew=not args.no_deskew,
                force=args.force_ocr
            )
            print(f"OCR output: {result}")
            engine.close()
            return
        except Exception as e:
            print(f"OCR Error: {e}")
            sys.exit(1)

    # Extract text
    if args.extract_text:
        if args.extract_text == "all":
            print(engine.get_all_text())
        else:
            page = int(args.extract_text) - 1
            print(engine.get_text(page))
        engine.close()
        return

    # Save
    output = args.output or args.input
    engine.save(output)
    print(f"Saved: {output}")
    engine.close()


# ═══════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} v{APP_VERSION} — MS Paint-style PDF Editor with Redaction & OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  GUI Mode:
    python pdf_paint.py
    python pdf_paint.py document.pdf

  CLI Redaction:
    python pdf_paint.py --cli -i doc.pdf --redact "page:1,x:50,y:100,w:200,h:30" -o redacted.pdf
    python pdf_paint.py --cli -i doc.pdf --redact-text "SSN" -o redacted.pdf
    python pdf_paint.py --cli -i doc.pdf --redact-text "1:John Doe" -o redacted.pdf

  CLI OCR:
    python pdf_paint.py --cli -i scanned.pdf --ocr -o searchable.pdf
    python pdf_paint.py --cli -i scanned.pdf --ocr --lang eng+fra -o searchable.pdf

  CLI Text Extract:
    python pdf_paint.py --cli -i doc.pdf --extract-text all
    python pdf_paint.py --cli -i doc.pdf --extract-text 1
        """
    )

    parser.add_argument("file", nargs="?", help="PDF file to open (GUI mode)")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no GUI)")
    parser.add_argument("-i", "--input", help="Input PDF file (CLI mode)")
    parser.add_argument("-o", "--output", help="Output PDF file")
    parser.add_argument("--redact", nargs="+", help='Redact areas: "page:1,x:50,y:100,w:200,h:30"')
    parser.add_argument("--redact-text", nargs="+", help='Redact text: "text" or "page:text"')
    parser.add_argument("--ocr", action="store_true", help="Run OCR on document")
    parser.add_argument("--lang", default="eng", help="OCR language (default: eng)")
    parser.add_argument("--no-deskew", action="store_true", help="Disable deskew during OCR")
    parser.add_argument("--force-ocr", action="store_true", help="Force OCR even if text exists")
    parser.add_argument("--extract-text", help='Extract text: "all" or page number')

    args = parser.parse_args()

    if args.cli:
        if not args.input:
            parser.error("--cli requires --input/-i")
        run_cli(args)
    else:
        if not HAS_GUI:
            print("ERROR: PyQt5 required for GUI mode. Run: pip install PyQt5")
            print("Or use --cli for headless operation.")
            sys.exit(1)

        app = QApplication(sys.argv)
        app.setStyle("Fusion")

        window = PDFPaintWindow(filepath=args.file)
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
