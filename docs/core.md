# Core Module — `app/core/`

The core module contains the foundational PDF processing logic that all other components depend on. It provides document management, rendering, annotation data models, and page manipulation operations.

---

## `pdf_document.py` — PDFDocument

**Purpose:** Wraps `fitz.Document` (PyMuPDF) with pending annotation storage and lifecycle management.

**Key Responsibilities:**
- Open/close PDF files via PyMuPDF
- Manage pending (in-memory) annotations per page
- Commit pending annotations to the PDF on save
- Incremental save for performance; full rewrite as fallback
- Track modified state for unsaved-changes prompts

**Public API:**

| Method/Property | Description |
|-----------------|-------------|
| `open(file_path)` | Open a PDF file, clearing previous state |
| `close()` | Close the document and release resources |
| `get_page(page_num)` | Return `fitz.Page` object by index |
| `add_pending_annotation(page, annot)` | Store annotation in memory (not yet saved) |
| `remove_pending_annotation(page, annot)` | Remove a pending annotation (for undo) |
| `get_pending_annotations(page)` | List pending annotations for a page |
| `get_all_pending_annotations()` | Dict of all pending annotations by page |
| `commit_annotations()` | Write all pending annotations to the PDF |
| `save(file_path=None)` | Commit + save (incremental or full) |
| `save_as(file_path, flatten=False)` | Save to new path, optionally flattening |
| `new_document()` | Create a blank PDF |
| `is_open` | Whether a document is loaded |
| `page_count` | Total number of pages |
| `modified` | Whether document has unsaved changes |
| `file_name` | Basename of the loaded file |

**Logging Coverage:**
- `INFO` on open, close, save (incremental/full/new path)
- `INFO` on commit annotations (count)

**Error Handling:**
- `IndexError` raised for out-of-range page access
- Silent `ValueError` catch on annotation removal (idempotent)
- Fallback from `saveIncr()` to full `save()` on incremental save failure

---

## `pdf_renderer.py` — Rendering & Coordinates

**Purpose:** Render PDF pages to PIL images and convert between canvas and PDF coordinate systems.

**Key Functions:**

| Function | Description |
|----------|-------------|
| `render_page(page, zoom)` | Render page to PIL Image at given zoom level |
| `render_thumbnail(page, width)` | Render a small thumbnail of a page |
| `canvas_to_pdf_coords(x, y, zoom)` | Convert screen pixels to PDF coordinates |
| `pdf_to_canvas_coords(x, y, zoom)` | Convert PDF coordinates to screen pixels |
| `get_render_scale(zoom)` | Get the scale factor for coordinate conversion |

**Constants:**
- `RENDER_DPI = 150` — Base rendering resolution (from `config.py`)

**Coordinate System:**
- PDF coordinates are in 72-DPI space
- Canvas coordinates are in `zoom * RENDER_DPI / 72` space
- The `_PageCanvasProxy` in `continuous_viewport.py` handles per-page offsets

**Logging Coverage:**
- None (pure stateless functions, errors propagate to callers)

---

## `annotation_model.py` — Annotation Data Structures

**Purpose:** Defines dataclasses for each annotation type and the logic to commit them to PDF.

**Annotation Types:**

| Class | Fields | fitz API Used |
|-------|--------|---------------|
| `RectAnnotation` | x0, y0, x1, y1, border_width, fill_color | `page.add_rect_annot()` |
| `CircleAnnotation` | x0, y0, x1, y1, border_width, fill_color | `page.add_circle_annot()` |
| `LineAnnotation` | x0, y0, x1, y1, border_width | `page.add_line_annot()` |
| `HighlightAnnotation` | quads (list of fitz.Quad) | `page.add_highlight_annot()` |
| `FreetextAnnotation` | x, y, text, font_size, text_color | `page.add_freetext_annot()` |
| `InkAnnotation` | points (list of tuples), border_width | `page.add_ink_annot()` |
| `ImageAnnotation` | x0, y0, x1, y1, image_path | `page.insert_image()` |
| `RedactAnnotation` | x0, y0, x1, y1 | `page.add_redact_annot()` |

**Base Class:** `AnnotationBase` — `page_num`, `color`, `opacity`

**Key Function:**
- `commit_to_pdf(page, annotation)` — Writes a single annotation to a fitz Page using the appropriate PyMuPDF API call

**Logging Coverage:**
- `DEBUG` on each annotation commit (type and page number)

---

## `page_operations.py` — PDF Page Manipulation

**Purpose:** Pure functions for page-level PDF operations (no UI dependencies).

**Functions:**

| Function | Description | Logging |
|----------|-------------|---------|
| `merge_pdfs(paths, output)` | Merge multiple PDFs into one | INFO: count + output path |
| `split_pdf(doc, ranges, dir, name)` | Split PDF by page ranges | INFO: part count + output dir |
| `rotate_page(doc, page, angle)` | Rotate a page by degrees | INFO: page + angle |
| `delete_pages(doc, pages)` | Delete specified pages | INFO: count + page numbers |
| `reorder_pages(doc, order)` | Reorder pages by index list | None |
| `insert_blank_page(doc, at, w, h)` | Insert a blank page | None |
| `insert_pages_from_file(doc, at, src)` | Insert pages from another PDF | None |
| `compress_pdf(doc, path, quality)` | Full compression with image downsampling | INFO: size before/after/savings |
| `compress_pdf_quick(doc, output)` | Quick compression (no image work) | None |

**Error Handling:**
- Image compression skips problematic images with `DEBUG` logging
- Temp file cleanup in `finally` block for compression

---

## Data Flow

```
User Action → Tool → AnnotationDataclass → PDFDocument._pending_annotations
                                                    ↓ (on save)
                                            commit_to_pdf() → fitz.Page API
                                                    ↓
                                            fitz.Document.save()
```
