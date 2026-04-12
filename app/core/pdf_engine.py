"""Core PDF operations — no GUI dependency.

Extracted from pdf_paint.py for use by both CLI and GUI modes.
"""
import os
import subprocess
import tempfile

try:
    import fitz
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False


class PDFEngine:
    """Headless PDF operations: redaction, OCR, text extraction, annotations."""

    def __init__(self, filepath=None):
        if not HAS_FITZ:
            raise ImportError("PyMuPDF (fitz) required. Install: pip install PyMuPDF")
        self.doc = None
        self.filepath = filepath
        self.annotations = {}
        if filepath:
            self.load(filepath)

    def load(self, filepath):
        self.filepath = filepath
        self.doc = fitz.open(filepath)
        return self

    def page_count(self):
        return len(self.doc) if self.doc else 0

    def get_page_pixmap(self, page_num, zoom=1.0):
        page = self.doc[page_num]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return pix

    def redact_area(self, page_num, x, y, w, h):
        page = self.doc[page_num]
        rect = fitz.Rect(x, y, x + w, y + h)
        page.add_redact_annot(rect, fill=(0, 0, 0))
        page.apply_redactions()
        return True

    def redact_text(self, page_num, search_text):
        page = self.doc[page_num]
        text_instances = page.search_for(search_text)
        for inst in text_instances:
            page.add_redact_annot(inst, fill=(0, 0, 0))
        page.apply_redactions()
        return len(text_instances)

    def add_text_annotation(self, page_num, x, y, text, fontsize=12, color=(0, 0, 0)):
        page = self.doc[page_num]
        point = fitz.Point(x, y)
        return page.insert_text(point, text, fontsize=fontsize, color=color)

    def draw_rect_annotation(self, page_num, x, y, w, h, color=(1, 0, 0), width=2, fill=None):
        page = self.doc[page_num]
        rect = fitz.Rect(x, y, x + w, y + h)
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=color, width=width, fill=fill)
        shape.commit()

    def draw_line_annotation(self, page_num, x1, y1, x2, y2, color=(0, 0, 0), width=2):
        page = self.doc[page_num]
        shape = page.new_shape()
        shape.draw_line(fitz.Point(x1, y1), fitz.Point(x2, y2))
        shape.finish(color=color, width=width)
        shape.commit()

    def draw_circle_annotation(self, page_num, cx, cy, r, color=(0, 0, 1), width=2, fill=None):
        page = self.doc[page_num]
        rect = fitz.Rect(cx - r, cy - r, cx + r, cy + r)
        shape = page.new_shape()
        shape.draw_oval(rect)
        shape.finish(color=color, width=width, fill=fill)
        shape.commit()

    def highlight_area(self, page_num, x, y, w, h, color=(1, 1, 0)):
        page = self.doc[page_num]
        rect = fitz.Rect(x, y, x + w, y + h)
        annot = page.add_highlight_annot(rect)
        annot.set_colors(stroke=color)
        annot.update()

    def ocr_document(self, output_path=None, language="eng", deskew=True, force=False):
        if not output_path:
            base, ext = os.path.splitext(self.filepath)
            output_path = f"{base}_ocr{ext}"

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
        page = self.doc[page_num]
        return page.get_text()

    def get_all_text(self):
        texts = []
        for i in range(len(self.doc)):
            texts.append(f"--- Page {i + 1} ---\n{self.get_text(i)}")
        return "\n\n".join(texts)
