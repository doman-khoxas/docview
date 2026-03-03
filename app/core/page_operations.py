"""Pure functions for PDF page manipulation."""
import os
import tempfile
import fitz
from pathlib import Path


def merge_pdfs(file_paths: list[str], output_path: str):
    result = fitz.open()
    for path in file_paths:
        doc = fitz.open(path)
        result.insert_pdf(doc)
        doc.close()
    result.save(output_path)
    result.close()


def split_pdf(doc: fitz.Document, page_ranges: list[tuple[int, int]], output_dir: str, base_name: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_files = []
    for i, (start, end) in enumerate(page_ranges):
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=end)
        out_path = output_dir / f"{base_name}_part{i + 1}.pdf"
        new_doc.save(str(out_path))
        new_doc.close()
        created_files.append(str(out_path))
    return created_files


def rotate_page(doc: fitz.Document, page_num: int, angle: int = 90):
    page = doc[page_num]
    page.set_rotation((page.rotation + angle) % 360)


def delete_pages(doc: fitz.Document, page_nums: list[int]):
    for num in sorted(page_nums, reverse=True):
        doc.delete_page(num)


def reorder_pages(doc: fitz.Document, new_order: list[int]):
    doc.select(new_order)


def insert_blank_page(doc: fitz.Document, at_index: int, width: float = 595, height: float = 842):
    doc.new_page(pno=at_index, width=width, height=height)


def insert_pages_from_file(doc: fitz.Document, at_index: int, source_path: str,
                           from_page: int = 0, to_page: int = -1):
    src = fitz.open(source_path)
    if to_page < 0:
        to_page = src.page_count - 1
    doc.insert_pdf(src, from_page=from_page, to_page=to_page, start_at=at_index)
    src.close()


# ---------------------------------------------------------------------------
# Compression
# ---------------------------------------------------------------------------

def compress_pdf(doc: fitz.Document, file_path: str,
                 image_quality: int = 75) -> dict:
    """
    Compress a PDF:
      1. garbage=4 — remove unused objects, deduplicate streams
      2. deflate=True — Flate-compress all streams
      3. clean=True — sanitize content streams
      4. Downscale large embedded images via Pillow

    Returns dict with before/after sizes and savings %.
    """
    original_size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0

    # --- Down-sample large images on each page ---
    for page_num in range(doc.page_count):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for img_info in image_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue
                img_bytes = base_image["image"]
                img_w = base_image.get("width", 0)
                img_h = base_image.get("height", 0)

                # Only downscale images bigger than ~1800px on longest side
                max_dim = max(img_w, img_h)
                if max_dim <= 1800:
                    continue

                from PIL import Image
                import io
                pil_img = Image.open(io.BytesIO(img_bytes))
                scale = 1800 / max_dim
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)

                buf = io.BytesIO()
                if pil_img.mode in ("RGBA", "P"):
                    pil_img = pil_img.convert("RGB")
                pil_img.save(buf, format="JPEG", quality=image_quality, optimize=True)
                new_bytes = buf.getvalue()

                # Only replace if actually smaller
                if len(new_bytes) < len(img_bytes):
                    page.replace_image(xref, stream=new_bytes)
            except Exception:
                continue  # Skip problematic images

    # --- Save with maximum compression ---
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(tmp_fd)
    new_size = original_size
    try:
        doc.save(tmp_path, garbage=4, deflate=True, clean=True)
        new_size = os.path.getsize(tmp_path)

        # Copy compressed file over the original
        if file_path:
            import shutil
            shutil.copy2(tmp_path, file_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    saved_pct = round((1 - (new_size / original_size)) * 100, 1) if original_size > 0 else 0.0
    return {
        "original_bytes": original_size,
        "compressed_bytes": new_size,
        "saved_pct": saved_pct
    }


def compress_pdf_quick(doc: fitz.Document, output_path: str) -> int:
    """
    Quick compression: garbage collection + deflate only (no image work).
    Returns compressed file size in bytes.
    """
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    return os.path.getsize(output_path)
