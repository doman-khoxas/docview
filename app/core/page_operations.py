"""Pure functions for PDF page manipulation."""
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
