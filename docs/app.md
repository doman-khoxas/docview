# Application Module — `app/`

Top-level application components that wire everything together.

---

## `app.py` — DocViewApp

**Purpose:** Root CTk application window — central hub connecting documents, tools, UI, and user actions.

**Key Responsibilities:**

| Area | Methods |
|------|---------|
| **File Operations** | `open_file_dialog()`, `open_file()`, `save_file()`, `save_file_as()`, `print_document()` |
| **Tab Management** | `switch_tab()`, `close_tab()` |
| **Tool Management** | `set_tool()` — instantiates/caches tool singletons |
| **Undo/Redo** | `push_undo()`, `undo()`, `redo()` — annotation-level undo |
| **Redaction** | `apply_redactions()`, `clear_redactions()` |
| **Status** | `update_status()` — refreshes status bar with current document info |
| **Overview** | `toggle_overview()` — shows all-pages grid |

**Tool Registry:**
```
select, text, highlight, rect, circle, line, freehand, redact, image
```

**Keyboard Shortcuts:**

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Open file |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save As |
| Ctrl+W | Close tab |
| Ctrl+F | Toggle search |
| Ctrl+Z | Undo |
| Ctrl+Y / Ctrl+Shift+Z | Redo |
| Ctrl+P | Print |
| Ctrl+B | Toggle sidebar |
| Ctrl+Plus/Minus | Zoom in/out |
| PgUp/PgDn, Left/Right | Navigate pages |
| Home/End | First/last page |
| Delete | Delete selected annotation |
| Escape | Deselect tool / close overlays |

**Logging Coverage:**
- `INFO` on app init, file open (with page count), file save, save-as
- `INFO` on print request, redaction application (with count)
- `DEBUG` on tool activation, undo push (type + stack size), save cancel
- `ERROR` on file open/save/print failures (with traceback)

---

## `document_manager.py` — DocumentManager

**Purpose:** Multi-document tab management with per-tab viewport state.

**TabState Fields:**
- `pdf_doc` — PDFDocument instance
- `file_path` — Path to the file
- `scroll_y` — Viewport scroll position
- `zoom` — Current zoom level
- `active_tool_name` — Selected tool name

**Key Methods:**

| Method | Description |
|--------|-------------|
| `open_document(path)` | Open in new tab or switch to existing tab |
| `close_tab(index)` | Close tab, adjust active index |
| `switch_tab(index)` | Switch active tab |
| `save_viewport_state()` | Persist scroll/zoom/tool for current tab |
| `has_unsaved_changes()` | Check if any tab has modifications |

**Logging Coverage:**
- `INFO` on document open in new tab (tab index + filename)
- `DEBUG` on switching to already-open document
- `INFO` on tab close (tab index + filename)

---

## `config.py` — Configuration Constants

**Purpose:** All hardcoded configuration values — colors, dimensions, defaults.

**Sections:**

| Section | Key Constants |
|---------|---------------|
| **Identity** | `WINDOW_TITLE`, `WINDOW_SIZE`, `APPEARANCE_MODE` |
| **Colors** | `BG_DEEP`, `BG_PANEL`, `BG_SURFACE`, `ACCENT`, `TEXT_PRIMARY`, etc. |
| **Layout** | `SIDEBAR_WIDTH=220`, `THUMBNAIL_WIDTH=150`, `PAGE_GAP=20` |
| **Zoom** | `ZOOM_DEFAULT=1.0`, `ZOOM_MIN=0.25`, `ZOOM_MAX=4.0`, `ZOOM_STEP=0.1` |
| **Rendering** | `RENDER_DPI=150`, `OVERSCAN_PX=200`, `PAGE_CACHE_SIZE=20` |
| **Annotations** | `DEFAULT_ANNOT_COLOR`, `DEFAULT_HIGHLIGHT_COLOR`, `DEFAULT_OPACITY=0.5` |
| **Search** | `SEARCH_HIGHLIGHT_COLOR`, `SEARCH_ACTIVE_COLOR` |

---

## `version.py` — Version Management

**Current Version:** `2.0.0` (Codename: "Brutalist")

**Feature Flags:**
```python
FEATURES = {
    "annotations": True,
    "page_management": True,
    "compression": True,
    "digital_signatures": True,
    "metadata_strip": True,
    "redaction": True,
    "drag_reorder": True,
    "multi_document": True,
    "search": True,
    "print": True,
}
```

---

## `recent_files.py` — RecentFiles

**Purpose:** JSON persistence for recently opened files list.

**Storage:** `~/.pdf_editor/recent_files.json`

**Features:**
- Maximum 10 recent files
- Validates file existence on load
- Deduplicates by resolved path
- Most recently opened first

---

## `logger.py` — Logging Infrastructure

**Purpose:** Centralized structured logging for crash diagnostics and operation tracking.

**Features:**
- Rotating file handler: 5 MB max, 3 backups
- Console output: WARNING+ to stderr
- Module-level loggers via `get_logger(__name__)`
- Session startup banner with Python version, platform, PID

**Log Location:** `~/.pdf_editor/logs/docview.log`

**Log Format:**
```
2026-03-04 12:00:00 | INFO     | docview.app.app              | File opened successfully: test.pdf (5 pages)
```

**Usage:**
```python
from app.logger import get_logger, log_exception
logger = get_logger(__name__)

logger.info("Document opened: %s", path)
logger.debug("Cache hit for page %d", page_num)
log_exception(logger, "Failed to save", exc)
```

---

## `main.py` — Entry Point

**Purpose:** Application entry point with crash logging.

**Flow:**
1. Initialize structured logging via `setup_logging()`
2. Import and instantiate `DocViewApp`
3. Open CLI-provided file if any
4. Enter `mainloop()`
5. On unhandled exception: write `crashlog.txt` + log to structured logger

**Crash Report Contents:**
- Timestamp, Python version, platform, CLI args
- Full traceback
- Written to both `crashlog.txt` (next to executable) and structured log
