# DocView

**Professional PDF Viewer, Editor & Annotator**

Built with CustomTkinter + PyMuPDF. Dark theme. Ribbon UI. Zero bloat.

---

## Overview

DocView is a lightweight, full-featured PDF editor designed to replace Adobe Reader and PDFgear. Built on a modular CustomTkinter architecture with a PyMuPDF engine, it offers professional-grade annotation, page management, compression, digital signatures, and redaction in a clean dark interface.

**Version 2.0.0** — Codename: *Brutalist*

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch
python main.py

# Open a specific file
python main.py document.pdf
```

## Build Standalone Executable

```bash
# One-click build (Windows)
docview-build.bat

# Manual build
pip install pyinstaller
python build.py           # Single executable
python build.py --onedir  # Directory bundle (faster startup)
python build.py --clean   # Clean + build
```

Output: `dist/DocView.exe` — no Python needed on target machine.

## Set as Default PDF Application

```bash
# Register DocView as a PDF handler (current user, no admin needed)
python install.py

# Or double-click:
install.bat

# Register for all users (requires admin)
python install.py --system

# Check registration status
python install.py --status

# Remove file associations
python install.py --uninstall
# Or double-click: uninstall.bat
```

After registering, go to **Windows Settings > Default Apps**, search for `.pdf`, and select **DocView**. You can also right-click any PDF > **Open With** > **DocView**.

The installer auto-detects whether to use the built `dist/DocView.exe` or the source `main.py` via `pythonw.exe`.

## Features

**Viewing**: Multi-document tabs, continuous viewport, page shadows, fit-to-width zoom, Ctrl+scroll zoom, keyboard navigation (arrows, PgUp/PgDn, Home/End), search (Ctrl+F).

**Annotations**: Freehand pen, highlighter, rectangle, circle, line, text box, image insertion. All with configurable color, opacity, border width, font size via properties panel. Undo/Redo (Ctrl+Z/Y). Double-click to edit text annotations.

**Page Management**: PDFgear-style Page tab with: New PDF, Insert Pages from file, Insert Blank Page, Extract Pages (dialog with range selection, one-PDF or separate-PDFs mode, delete-after-extraction), Delete Pages, Rotate Left/Right. Page range input field (eg. 1,8,10-12). Document overview grid with multi-select and drag-and-drop reorder.

**Compression**: Downscales large embedded images via Pillow + PDF-level garbage collection, deflate, and stream cleanup. Shows before/after size comparison.

**Security**: Redaction tool with preview and batch apply. Metadata stripping (OPSEC: removes author, title, dates, XMP). Digital signatures via PFX/P12 certificates (endesive) or visible stamp.

**Printing**: Ctrl+P sends to OS print system.

## Version Management

```bash
python update.py status              # Show version + features
python update.py bump patch          # 2.0.0 -> 2.0.1
python update.py bump minor          # 2.0.0 -> 2.1.0
python update.py bump major          # 2.0.0 -> 3.0.0
python update.py changelog "message" # Add changelog entry
python update.py release minor "msg" # Full release prep
python update.py history             # Show changelog
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+O | Open file |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save As |
| Ctrl+W | Close tab |
| Ctrl+Z | Undo |
| Ctrl+Y / Ctrl+Shift+Z | Redo |
| Ctrl+F | Search |
| Ctrl+P | Print |
| Ctrl+B | Toggle sidebar |
| Ctrl+Scroll | Zoom in/out |
| Ctrl+Plus/Minus | Zoom in/out |
| Left/Right | Previous/Next page |
| PgUp/PgDn | Previous/Next page |
| Home/End | First/Last page |
| Up/Down | Scroll viewport |
| Delete | Delete selected annotation |
| Escape | Deselect tool / close overlay |

## Project Structure

```
docview/
├── main.py                  # Entry point with crash logging
├── install.py               # File association installer (Windows)
├── install.bat              # Double-click to register as PDF handler
├── uninstall.bat            # Double-click to remove associations
├── update.py                # Version management utility
├── build.py                 # PyInstaller build script
├── docview-build.bat        # One-click Windows build
├── docview.bat              # Quick-launch batch
├── requirements.txt         # Dependencies
├── CHANGELOG.md             # Version history
├── app/
│   ├── app.py               # Root CTk application
│   ├── config.py            # Theme colors, geometry, defaults
│   ├── version.py           # Semantic version + feature flags
│   ├── document_manager.py  # Multi-tab document management
│   ├── recent_files.py      # MRU file list
│   ├── core/
│   │   ├── pdf_document.py      # PyMuPDF wrapper + annotation storage
│   │   ├── pdf_renderer.py      # Page rendering + thumbnails
│   │   ├── annotation_model.py  # Annotation types + PDF commit
│   │   └── page_operations.py   # Merge, split, rotate, compress
│   ├── tools/
│   │   ├── base_tool.py         # Abstract base for all tools
│   │   ├── select_tool.py       # Select + move annotations
│   │   ├── hand_tool.py         # Pan viewport
│   │   ├── text_tool.py         # Text box annotations
│   │   ├── freehand_tool.py     # Freehand pen drawing
│   │   ├── highlight_tool.py    # Highlight regions
│   │   ├── rect_tool.py         # Rectangle annotations
│   │   ├── circle_tool.py       # Circle annotations
│   │   ├── line_tool.py         # Line annotations
│   │   ├── image_tool.py        # Image insertion
│   │   └── redact_tool.py       # Redaction rectangles
│   └── ui/
│       ├── main_window.py       # Layout: sidebar + viewport + panels
│       ├── toolbar.py           # Ribbon toolbar (Home/Edit/Page/Tools)
│       ├── sidebar.py           # Thumbnail sidebar with context menu
│       ├── continuous_viewport.py # PDF page rendering canvas
│       ├── tab_bar.py           # Multi-document tab strip
│       ├── overview_panel.py    # Page grid with drag-drop reorder
│       ├── properties_panel.py  # Annotation property editor
│       ├── search_panel.py      # Find in document
│       ├── status_bar.py        # Page info + zoom + sidebar toggle
│       ├── welcome_screen.py    # Empty state landing
│       ├── context_menu.py      # Right-click menus
│       ├── extract_dialog.py    # PDFgear-style extract pages dialog
│       ├── sign_dialog.py       # Digital signature dialog
│       ├── about_dialog.py      # Version + feature info
│       └── dialogs/             # Additional dialog windows
└── assets/
    ├── docview.ico              # Application icon
    └── generate_icon.py         # Icon generation script
```

## Requirements

- Python 3.10+
- PyMuPDF >= 1.23
- CustomTkinter >= 5.2.0
- Pillow >= 10.0
- (Optional) endesive + cryptography — for cryptographic PDF signing

## License

MIT

---

*Operator Systems // BLACK TECH WIZARD Build*
