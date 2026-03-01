# DocView

**MS Paint-inspired PDF Editor with Redaction, OCR & Full Annotation Suite**

Built by Operator Systems // BLACK TECH WIZARD

---

## Overview

DocView is a cross-platform PDF editing tool with a Windows 7 Paint-style ribbon interface. It supports freehand drawing, shapes, text annotations, document redaction, and OCR via ocrmypdf. It also ships with a full CLI mode for headless operation in Claude Code and automation pipelines.

**Version 1.0**

## Architecture

DocView ships with two interface options, both powered by PyMuPDF:

| Entry Point | Stack | Best For |
|-------------|-------|----------|
| `pdf_paint.py` | PyQt5 | Primary — Paint-style ribbon UI, redaction, OCR, CLI mode |
| `main.py` + `app/` | CustomTkinter | Alternative — multi-tab editor with continuous viewport |

## Features

### GUI Mode (pdf_paint.py)
- Windows 7 ribbon-style toolbar with grouped tool sections
- **Drawing Tools**: Pen, Highlighter, Eraser, Text
- **Shapes**: Rectangle, Circle, Line, Arrow
- **Redaction**: Area select (draw rectangles), text search redaction, preview before apply
- **OCR**: Full document OCR via ocrmypdf with language support
- **Text Extraction**: Pull text from any page
- **Color Picker** and adjustable pen sizes
- **Zoom**: 25% to 400%
- **Page Navigation**: Multi-page support with prev/next
- **Keyboard Shortcuts**: Ctrl+O, Ctrl+S, Ctrl+Z, Ctrl+/- zoom

### CLI Mode (for Claude Code)
```bash
# Redact an area
python pdf_paint.py --cli -i doc.pdf --redact "page:1,x:50,y:100,w:200,h:30" -o redacted.pdf

# Redact by text search
python pdf_paint.py --cli -i doc.pdf --redact-text "SSN" -o redacted.pdf

# Run OCR
python pdf_paint.py --cli -i scanned.pdf --ocr -o searchable.pdf

# Extract text
python pdf_paint.py --cli -i doc.pdf --extract-text all
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch GUI
python pdf_paint.py

# Open a specific file
python pdf_paint.py document.pdf

# CLI mode (headless)
python pdf_paint.py --cli -i input.pdf --ocr -o output.pdf
```

## Build Executable

Package everything into a single standalone executable:

```bash
# Install build dependency
pip install pyinstaller

# Build single executable
python build.py

# Build as directory bundle (faster startup)
python build.py --onedir

# Clean + build
python build.py --clean
```

Output lands in `dist/DocView` (or `dist/DocView.exe` on Windows). No Python installation needed on the target machine.

## Requirements

- Python 3.9+
- PyQt5 >= 5.15
- PyMuPDF >= 1.23
- ocrmypdf >= 16.0 (for OCR)
- Pillow >= 10.0

## Project Structure

```
docview/
├── pdf_paint.py          # v2: PyQt5 Paint-style editor (GUI + CLI)
├── main.py               # v1: CustomTkinter editor entry point
├── app/
│   ├── app.py            # v1 root application
│   ├── config.py         # Shared constants
│   ├── core/
│   │   ├── pdf_document.py
│   │   ├── pdf_renderer.py
│   │   ├── annotation_model.py
│   │   └── page_operations.py
│   ├── tools/
│   │   ├── base_tool.py
│   │   ├── freehand_tool.py
│   │   ├── highlight_tool.py
│   │   ├── text_tool.py
│   │   ├── rect_tool.py
│   │   ├── circle_tool.py
│   │   ├── line_tool.py
│   │   ├── select_tool.py
│   │   └── hand_tool.py
│   └── ui/
│       ├── main_window.py
│       ├── toolbar.py
│       ├── sidebar.py
│       ├── continuous_viewport.py
│       ├── tab_bar.py
│       ├── properties_panel.py
│       ├── search_panel.py
│       ├── status_bar.py
│       └── dialogs/
├── build.py              # PyInstaller build script → single executable
├── requirements.txt
├── .gitignore
├── SETUP_REPO.sh         # One-click GitHub repo creation
└── README.md
```

## Changelog

### v1.0 — DocView (Current)
- Windows 7 Paint-style ribbon toolbar (PyQt5)
- Full annotation suite: Pen, Highlighter, Eraser, Text, Shapes
- Redaction tool (area select + text search)
- OCR integration via ocrmypdf
- CLI mode for Claude Code headless operation
- Text extraction from any page
- PyInstaller single-executable packaging (cross-platform)
- Multi-tab modular editor (CustomTkinter alternative)
- UX Design Critique Checklist template

## License

MIT

---

*Operator Systems // BLACK TECH WIZARD Build*
