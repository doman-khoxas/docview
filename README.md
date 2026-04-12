# DocView

**Document Viewer & Editor -- PDF, Markdown, Obsidian Integration**

Built by Operator Systems // BLACK TECH WIZARD

---

## Overview

DocView is a cross-platform document viewer and editor built on PyQt5. It handles PDFs with full annotation and redaction tools, opens and edits Markdown files with live preview, integrates with Obsidian vaults for wikilink navigation, and includes desktop sticky notes accessible from the system tray.

**Version 2.0.0**

## Features

### PDF Viewer & Editor
- QGraphicsView-based viewport with smooth zoom and continuous scroll
- **Drawing Tools**: Select, Hand, Pen, Highlighter, Text, Rectangle, Circle, Line
- **Redaction**: Area select and text search redaction with permanent removal
- **OCR**: Full document OCR via ocrmypdf with language support
- **Text Extraction**: Pull text from any page or all pages
- **Page Operations**: Rotate, delete, insert blank/from file, merge, split
- Multi-tab document editing with per-tab state

### Markdown Editor
- Syntax highlighting for headers, bold, italic, code, wikilinks, frontmatter, tags
- Line numbers with current-line highlighting
- Live HTML preview with debounced updates (split pane)
- YAML frontmatter parsing and display
- Clickable `[[wikilinks]]` that open target files in new tabs

### Obsidian Integration
- Vault browser sidebar with file tree filtered to `.md` files
- Wikilink resolution matching Obsidian behavior (case-insensitive, shortest path)
- Backlink detection across vault
- Copy wikilink from context menu
- QFileSystemWatcher for live vault changes
- Configurable vault path via Settings dialog

### Desktop Sticky Notes
- System tray icon with right-click menu: New Note, Show All, Hide All
- Frameless floating windows with draggable title bars
- 6 color options (yellow, blue, green, pink, orange, purple)
- Auto-save with 500ms debounce
- Persisted as `.md` files with YAML frontmatter at `~/.docview/sticky-notes/`
- Position, size, and color restored on startup

### UI
- VS Code-inspired dark theme (Fusion + custom QPalette + QSS)
- Flat toolbar with tool buttons and document action dropdowns
- Sidebar with Pages, TOC, Notes, and Vault tabs
- Properties panel for annotation styling (color, opacity, font, border)
- Status bar with page entry, zoom slider, file info

### CLI Mode
```bash
# Redact an area
python docview.py --cli -i doc.pdf --redact "page:1,x:50,y:100,w:200,h:30" -o redacted.pdf

# Redact by text search
python docview.py --cli -i doc.pdf --redact-text "SSN" -o redacted.pdf

# Run OCR
python docview.py --cli -i scanned.pdf --ocr -o searchable.pdf

# Extract text
python docview.py --cli -i doc.pdf --extract-text all
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch GUI
python docview.py

# Open a PDF
python docview.py document.pdf

# Open a Markdown file
python docview.py notes.md

# CLI mode (headless)
python docview.py --cli -i input.pdf --ocr -o output.pdf

# Version
python docview.py --version
```

## Build & Install

### Portable Executable

```bash
pip install pyinstaller

# Single executable
python build.py

# Directory bundle (faster startup)
python build.py --onedir

# Clean + build
python build.py --clean
```

### Windows Installer

Requires [Inno Setup 6](https://jrsoftware.org/isdl.php) installed.

```bash
# One command: builds app + compiles installer
python build.py --installer

# Output: DocView_2.0.0_Setup.exe
```

The installer provides:
- Start Menu and Desktop shortcuts
- Optional `.pdf` and `.md` file associations
- "Open With" integration in Windows Explorer
- Clean uninstaller via Add/Remove Programs
- System tray icon for sticky notes

### Regenerate Icon

```bash
python build.py --icon
```

Output: `dist/DocView.exe` (portable) or `DocView_2.0.0_Setup.exe` (installer).

## Requirements

- Python 3.9+
- PyQt5 >= 5.15
- PyMuPDF >= 1.23
- ocrmypdf >= 16.0 (for OCR)
- Pillow >= 10.0
- markdown >= 3.5
- pyyaml >= 6.0

## Project Structure

```
docview/
+-- docview.py                    # Unified entry point (GUI + CLI)
+-- cli.py                        # CLI engine (redaction, OCR, text extraction)
+-- build.py                      # PyInstaller build script
+-- app/
|   +-- version.py                # Version info
|   +-- config.py                 # All constants and configuration
|   +-- document_manager.py       # Multi-tab state management
|   +-- recent_files.py           # JSON persistence for recent files
|   +-- core/
|   |   +-- document.py           # Document ABC
|   |   +-- pdf_document.py       # PDF implementation (PyMuPDF)
|   |   +-- markdown_document.py  # Markdown implementation
|   |   +-- pdf_engine.py         # Headless PDF operations
|   |   +-- pdf_renderer.py       # Rendering utilities
|   |   +-- annotation_model.py   # Annotation dataclasses
|   |   +-- page_operations.py    # Merge, split, rotate, delete, insert
|   |   +-- obsidian/
|   |       +-- vault.py          # Vault indexing and file watching
|   |       +-- wikilinks.py      # Wikilink parsing and resolution
|   |       +-- frontmatter.py    # YAML frontmatter parse/serialize
|   +-- tools/
|   |   +-- base_tool.py          # Tool ABC (QGraphicsScene events)
|   |   +-- select_tool.py        # Move/delete annotations
|   |   +-- hand_tool.py          # Pan viewport
|   |   +-- text_tool.py          # Click-to-place text
|   |   +-- highlight_tool.py     # Text-snapping highlight
|   |   +-- rect_tool.py          # Rectangle shapes
|   |   +-- circle_tool.py        # Ellipse shapes
|   |   +-- line_tool.py          # Line annotations
|   |   +-- freehand_tool.py      # Ink drawing with decimation
|   |   +-- redact_tool.py        # Area redaction
|   +-- ui/
|       +-- app.py                # QApplication with dark theme + system tray
|       +-- theme.py              # Dark palette and QSS stylesheet
|       +-- main_window.py        # QMainWindow orchestrator
|       +-- toolbar.py            # Flat toolbar with tool buttons
|       +-- tab_bar.py            # QTabBar for documents
|       +-- status_bar.py         # Zoom slider, page entry, file info
|       +-- welcome_screen.py     # Start screen with recent files
|       +-- properties_panel.py   # Annotation styling panel
|       +-- search_panel.py       # Ctrl+F search bar
|       +-- context_menu.py       # Right-click menu
|       +-- sidebar/
|       |   +-- sidebar_panel.py  # Tabbed sidebar container
|       |   +-- vault_browser.py  # Obsidian vault file tree
|       +-- viewport/
|       |   +-- pdf_viewport.py   # QGraphicsView PDF renderer
|       |   +-- pdf_page_item.py  # Per-page QGraphicsPixmapItem
|       +-- editor/
|       |   +-- editor_widget.py  # Split pane: editor + preview
|       |   +-- markdown_editor.py    # QPlainTextEdit with line numbers
|       |   +-- markdown_highlighter.py  # QSyntaxHighlighter
|       |   +-- markdown_preview.py   # QTextBrowser HTML preview
|       +-- sticky/
|       |   +-- sticky_note.py    # Frameless floating note widget
|       |   +-- sticky_manager.py # Note lifecycle and persistence
|       +-- dialogs/
|           +-- settings_dialog.py    # Vault path and preferences
|           +-- merge_dialog.py       # PDF merge
|           +-- split_dialog.py       # PDF split
|           +-- export_dialog.py      # Export with flatten option
|           +-- insert_page_dialog.py # Insert blank/from file
+-- requirements.txt
+-- CHANGELOG.md
+-- .gitignore
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Open file |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save As |
| Ctrl+W | Close tab |
| Ctrl+F | Search |
| Ctrl+= / Ctrl+- | Zoom in/out |
| Ctrl+0 | Fit width |
| PgUp / PgDown | Previous/next page |
| Home / End | First/last page |
| Escape | Deselect tool |
| Delete | Delete selected annotation |

## License

MIT

---

*Operator Systems // BLACK TECH WIZARD Build*
