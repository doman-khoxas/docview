# UI Module — `app/ui/`

The UI module implements all visual components using CustomTkinter (modern themed Tkinter). Components follow a hierarchical layout assembled by `MainWindow`.

---

## Layout Hierarchy

```
DocViewApp (CTk root window)
├── Toolbar (ribbon tabs: Home | Edit | Page | Tools)
├── TabBar (multi-document tabs)
├── MiddleFrame
│   ├── Sidebar (PAGES | TOC | NOTES tabs)
│   ├── CenterContainer
│   │   ├── SearchPanel (Ctrl+F, initially hidden)
│   │   ├── WelcomeScreen (shown when no document open)
│   │   ├── ContinuousViewport (main PDF canvas)
│   │   └── OverviewPanel (floating grid view)
│   └── PropertiesPanel (annotation property editor, hidden by default)
├── ContextMenu (right-click menu)
└── StatusBar (filename, page number, zoom percentage)
```

---

## `main_window.py` — MainWindow

**Purpose:** Assembles all UI panels into the application layout.

| Method | Description |
|--------|-------------|
| `show_document()` | Switch from welcome screen to viewport, load document |
| `show_welcome()` | Switch back to welcome screen (all tabs closed) |

**Component References:**
- `toolbar`, `tab_bar`, `sidebar`, `viewport`, `status_bar`
- `search_panel`, `properties_panel`, `context_menu`, `overview_panel`, `welcome_screen`

---

## `toolbar.py` — Toolbar (Ribbon UI)

**Purpose:** PDFgear/Windows 11 Paint-style ribbon toolbar with 4 category tabs.

**Tab Categories:**

| Tab | Groups | Key Actions |
|-----|--------|-------------|
| **Home** | File, Edit, View, Navigate, Mode, Info | Open, Save, SaveAs, Print, Undo, Redo, Zoom, Prev/Next, Select/Hand, About |
| **Edit** | Draw, Shapes, Text, Insert | Pen, Highlight, Rect, Circle, Line, Text, Image tools |
| **Page** | Insert, Manage, Rotate, Optimize, PageRange | New PDF, Insert, Blank, Extract, Delete, Rotate L/R, Compress, PageRange field |
| **Tools** | Redaction, Security, OCR | Redact/Apply/Clear, Sign, StripMeta, OCR placeholder |

**Components:**
- `_RibbonButton` — Compound widget: large Unicode symbol + small label
- `_group()` — Creates labeled tool group
- `_separator()` — Thin vertical divider between groups

**Logging Coverage:**
- `INFO` on metadata strip (start + success)
- `ERROR` on compression failure

---

## `html_viewport.py` — HTMLViewport

**Purpose:** Renders HTML and Markdown files locally within the app using `tkhtmlview`.

**Features:**
- Renders `.html`, `.htm` files with native HTML rendering
- Converts `.md`, `.markdown` files to HTML via Python `markdown` module
- Dark theme CSS automatically injected (matching DocView's color palette)
- Styled headings, code blocks, tables, blockquotes, lists
- Supports `tables`, `fenced_code`, `codehilite`, `toc`, `nl2br` markdown extensions
- Plain text fallback for unsupported files

**File Type Routing:**
- `app.py:open_file()` checks file extension before routing
- HTML/MD files go to `main_window.show_html(path)`
- PDF files go to `main_window.show_document()` as before

**Logging Coverage:**
- `INFO` on HTML/MD/text file load (filename + char count)
- `WARNING` if markdown module unavailable

---

## `continuous_viewport.py` — ContinuousViewport

**Purpose:** Main PDF canvas with continuous vertical scrolling, lazy rendering, and LRU page cache.

**Architecture:**
- All pages stacked vertically with `PAGE_GAP` spacing
- Only visible pages (+ `OVERSCAN_PX` buffer) are rendered
- `PAGE_CACHE_SIZE=20` LRU cache for rendered images
- `_PageCanvasProxy` — Wraps tk.Canvas to offset drawing commands per-page

**Key Methods:**

| Method | Description |
|--------|-------------|
| `load_document()` | Compute layout, clear cache, render visible pages |
| `render_current_page()` | Re-render current page (after annotation change) |
| `go_to_page(n)` | Scroll to page n |
| `zoom_in/out()` | Adjust zoom level (debounced 100ms) |
| `canvas_to_page_coords(cx, cy)` | Convert canvas coords to `(page_num, pdf_x, pdf_y)` |
| `highlight_search_results(results)` | Draw yellow rectangles for search matches |

**Event Handling:**
- Mouse press/drag/release → delegated to active tool (with page-relative coords)
- Hand tool / no tool → pan with `scan_mark`/`scan_dragto`
- MouseWheel → scroll; Ctrl+MouseWheel → zoom
- Double-click → edit FreetextAnnotation in-place

**Performance Features:**
- Debounced configure events (80ms)
- Debounced zoom operations (100ms)
- LRU eviction skips pages currently drawn on canvas

**Logging Coverage:**
- `DEBUG` on document load (page count + zoom level)

---

## `sidebar.py` — Sidebar

**Purpose:** Three-tab sidebar with page thumbnails, table of contents, and annotation list.

**Tabs:**

| Tab | Key | Content |
|-----|-----|---------|
| PAGES | `thumbnails` | Page thumbnail grid with click-to-navigate |
| TOC | `bookmarks` | Table of contents from `doc.get_toc()` |
| NOTES | `annotations` | List of pending annotations by page |

**Features:**
- Lazy thumbnail loading for documents > 20 pages
- Right-click context menu on thumbnails (Extract, Rotate, Insert Blank, Delete)
- Active page highlighting with accent border
- Toggle visibility with Ctrl+B

**Logging Coverage:**
- `DEBUG` on TOC load (entry count)
- `WARNING` on TOC load failure
- `INFO` on page extraction success
- `ERROR` on extraction failure

---

## `search_panel.py` — SearchPanel

**Purpose:** Ctrl+F search bar with prev/next result navigation.

**Search Flow:**
1. User types query + Enter/Find
2. Iterates all pages: `page.search_for(query)`
3. Results stored as `[(page_num, [Rect, ...]), ...]`
4. Flattened to `[(page_num, rect_idx), ...]` for navigation
5. Yellow highlight rectangles drawn on canvas

**Logging Coverage:**
- `INFO` on search (query, result count, page count)

**Current Limitations:**
- Case-sensitive only (no toggle)
- No regex support

---

## `properties_panel.py` — PropertiesPanel

**Purpose:** Annotation property editor (color, opacity, stroke width, fill, font settings).

**Properties Exposed:**
- `stroke_color` — Annotation border/stroke color
- `highlight_color` — Highlight annotation color
- `fill_color` — Shape fill color (optional)
- `opacity` — Annotation opacity (0.0-1.0)
- `border_width` — Stroke width in points
- `font_size` — Text annotation font size
- `text_color` — Text annotation color

---

## `status_bar.py` — StatusBar

**Purpose:** Bottom bar showing filename, page number (editable), and zoom percentage.

**Features:**
- Click page number to type and jump to specific page
- Displays filename and total page count

---

## `overview_panel.py` — OverviewPanel

**Purpose:** Floating grid view of all pages for multi-select operations.

**Features:**
- Grid layout with configurable columns
- Multi-select for extraction/deletion
- Extract and delete buttons in toolbar
- Reorder by drag (future)

---

## `tab_bar.py` — TabBar

**Purpose:** Multi-document tab management with close buttons.

---

## `welcome_screen.py` — WelcomeScreen

**Purpose:** Landing screen shown when no documents are open, with recent files list.

---

## Dialogs (`app/ui/dialogs/`)

| Dialog | Purpose |
|--------|---------|
| `text_input_dialog.py` | Simple text entry dialog for annotations |
| `export_dialog.py` | Export current page as image |
| `merge_dialog.py` | Merge multiple PDFs |
| `split_dialog.py` | Split PDF by page ranges |
| `insert_page_dialog.py` | Insert pages from another PDF |

## Other Dialogs

| Dialog | Purpose |
|--------|---------|
| `about_dialog.py` | Version info, features, and changelog |
| `extract_dialog.py` | Advanced page extraction with range input |
| `sign_dialog.py` | Digital signature (CAC/certificate) dialog |
| `context_menu.py` | Right-click context menu for viewport |
