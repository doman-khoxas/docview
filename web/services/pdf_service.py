"""Document lifecycle management — bridges Flask routes to DocView core."""

import atexit
import io
import os
import uuid

from PIL import Image

from app.core.pdf_engine import PDFEngine
from app.core.page_operations import (
    merge_pdfs,
    rotate_page,
    delete_pages,
    reorder_pages,
)
from web.config import UPLOAD_FOLDER, DEFAULT_JPEG_QUALITY

# In-memory registry: doc_id -> (PDFEngine, original_filename)
_documents: dict[str, tuple[PDFEngine, str]] = {}


def upload_pdf(file_storage) -> dict:
    """Save uploaded file, open with PDFEngine, return doc metadata."""
    doc_id = uuid.uuid4().hex[:12]
    filename = file_storage.filename or "document.pdf"
    save_path = os.path.join(UPLOAD_FOLDER, f"{doc_id}.pdf")

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_storage.save(save_path)

    engine = PDFEngine(save_path)
    _documents[doc_id] = (engine, filename)

    return {
        "id": doc_id,
        "filename": filename,
        "pages": engine.page_count(),
    }


def get_info(doc_id: str) -> dict:
    engine, filename = _get(doc_id)
    return {
        "id": doc_id,
        "filename": filename,
        "pages": engine.page_count(),
    }


def list_documents() -> list[dict]:
    return [
        {"id": did, "filename": fname, "pages": eng.page_count()}
        for did, (eng, fname) in _documents.items()
    ]


def render_page_jpeg(doc_id: str, page_num: int, zoom: float = 1.0) -> bytes:
    engine, _ = _get(doc_id)
    pix = engine.get_page_pixmap(page_num, zoom=zoom)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=DEFAULT_JPEG_QUALITY)
    return buf.getvalue()


def extract_text(doc_id: str, page_num: int) -> str:
    engine, _ = _get(doc_id)
    return engine.get_text(page_num)


def extract_all_text(doc_id: str) -> str:
    engine, _ = _get(doc_id)
    return engine.get_all_text()


def get_page_count(doc_id: str) -> int:
    engine, _ = _get(doc_id)
    return engine.page_count()


def do_rotate(doc_id: str, page_num: int, angle: int = 90) -> int:
    engine, _ = _get(doc_id)
    rotate_page(engine.doc, page_num, angle)
    _save_current(engine)
    return engine.page_count()


def do_delete(doc_id: str, page_nums: list[int]) -> int:
    engine, _ = _get(doc_id)
    delete_pages(engine.doc, page_nums)
    _save_current(engine)
    return engine.page_count()


def do_reorder(doc_id: str, new_order: list[int]) -> int:
    engine, _ = _get(doc_id)
    reorder_pages(engine.doc, new_order)
    _save_current(engine)
    return engine.page_count()


def do_merge(doc_ids: list[str]) -> dict:
    paths = []
    for did in doc_ids:
        engine, _ = _get(did)
        # Save current state so merge reads latest
        _save_current(engine)
        paths.append(engine.filepath)

    merged_id = uuid.uuid4().hex[:12]
    merged_path = os.path.join(UPLOAD_FOLDER, f"{merged_id}.pdf")
    merge_pdfs(paths, merged_path)

    engine = PDFEngine(merged_path)
    _documents[merged_id] = (engine, "merged.pdf")
    return {
        "id": merged_id,
        "filename": "merged.pdf",
        "pages": engine.page_count(),
    }


def get_download_path(doc_id: str) -> tuple[str, str]:
    """Return (file_path, filename) for download."""
    engine, filename = _get(doc_id)
    _save_current(engine)
    return engine.filepath, filename


def do_ocr(doc_id: str, language: str = "eng") -> dict:
    """Run OCR on a document, replace it with the OCR'd version."""
    engine, filename = _get(doc_id)
    _save_current(engine)

    base, ext = os.path.splitext(engine.filepath)
    ocr_path = f"{base}_ocr{ext}"

    _run_ocr(engine.filepath, ocr_path, language)

    # Close old engine, open the OCR'd file
    engine.close()
    ocr_engine = PDFEngine(ocr_path)

    base_name, ext_name = os.path.splitext(filename)
    ocr_filename = f"{base_name}_ocr{ext_name}"
    _documents[doc_id] = (ocr_engine, ocr_filename)

    return {
        "id": doc_id,
        "filename": ocr_filename,
        "pages": ocr_engine.page_count(),
    }


def ocr_oneshot(file_storage, language: str = "eng") -> tuple[str, str]:
    """Upload → OCR → return path to OCR'd file.

    Optimized for screenshot-captured PDFs: skips deskew, uses
    force-ocr (no text layer exists), parallelizes across cores.
    """
    doc_id = uuid.uuid4().hex[:12]
    filename = file_storage.filename or "capture.pdf"
    save_path = os.path.join(UPLOAD_FOLDER, f"{doc_id}.pdf")
    base, ext = os.path.splitext(filename)
    ocr_path = os.path.join(UPLOAD_FOLDER, f"{doc_id}_ocr.pdf")

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_storage.save(save_path)

    try:
        _run_ocr(save_path, ocr_path, language)
    finally:
        if os.path.exists(save_path):
            os.unlink(save_path)

    return ocr_path, f"{base}_ocr{ext}"


def _run_ocr(input_path: str, output_path: str, language: str = "eng"):
    """Run ocrmypdf optimized for screenshot PDFs."""
    import subprocess

    # Normalize to absolute OS-native paths (ocrmypdf needs this on Windows)
    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)

    cmd = [
        "ocrmypdf",
        "--force-ocr",              # screenshots have no text layer
        "--optimize", "1",          # lossless optimization
        "--jobs", "4",              # parallel page processing
        "--tesseract-timeout", "60",
        "--output-type", "pdf",
    ]
    if language:
        cmd.extend(["-l", language])
    cmd.extend([input_path, output_path])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"OCR failed: {result.stderr.strip()}")


def close_document(doc_id: str) -> None:
    if doc_id not in _documents:
        return
    engine, _ = _documents.pop(doc_id)
    filepath = engine.filepath
    engine.close()
    if filepath and os.path.exists(filepath):
        os.unlink(filepath)


def cleanup_all() -> None:
    for doc_id in list(_documents.keys()):
        close_document(doc_id)


# --- internal helpers ---

def _get(doc_id: str) -> tuple[PDFEngine, str]:
    if doc_id not in _documents:
        raise KeyError(f"Document '{doc_id}' not found")
    return _documents[doc_id]


def _save_current(engine: PDFEngine) -> None:
    """Persist current state to disk (incremental save)."""
    engine.save()


atexit.register(cleanup_all)
