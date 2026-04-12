# Changelog

## [2.0.0] - 2026-04-12

### Architecture
- Consolidated from dual-stack (PyQt5 + CustomTkinter) to PyQt5 only
- Introduced Document ABC with PDFDocument and MarkdownDocument implementations
- Extracted PDFEngine from monolithic pdf_paint.py into standalone module
- Modular tool system ported to QGraphicsScene event model

### Added
- **Markdown Editor**: Full editor with syntax highlighting, line numbers, live preview
  - QSyntaxHighlighter supporting headers, bold, italic, code, wikilinks, frontmatter
  - Split-pane editor + HTML preview with debounced updates
- **Obsidian Integration**: Vault browser, wikilink resolution, backlinks
  - QFileSystemModel-based vault browser with search filtering
  - Wikilink parsing and resolution matching Obsidian behavior
  - YAML frontmatter parsing/serialization
  - Clickable wikilinks in preview that open target files
  - Settings dialog for vault path configuration
- **Sticky Notes**: Desktop sticky notes with system tray integration
  - Right-click tray icon to create/manage notes
  - Frameless floating windows with custom title bars
  - Color selection (yellow, blue, green, pink, orange, purple)
  - Auto-save with debounce, persisted as .md files with YAML frontmatter
  - Position/size restoration on startup
- **Dark Theme**: VS Code-inspired dark palette with comprehensive QSS
- **Redact Tool**: Proper BaseTool subclass for PDF area redaction
- **Context Menu**: Right-click on viewport for quick access to tools and page ops
- **Settings Dialog**: Vault path, editor font size, tab size configuration

### Changed
- Entry point: `docview.py` (replaces `pdf_paint.py` and `main.py`)
- PDF viewport: QGraphicsView + QGraphicsScene (replaces QLabel/Canvas)
- Config stored at `~/.docview/` (replaces `~/.pdf_editor/`)
- File dialogs accept both .pdf and .md files
- Sidebar includes Vault browser tab alongside Pages/TOC/Notes

### Removed
- CustomTkinter dependency and all tkinter-based code
- Windows 7 Paint ribbon toolbar style
- `pdf_paint.py` (monolithic v2 entry point)
- `main.py` (v1 CustomTkinter entry point)
- `app/app.py` (CustomTkinter root application)
- `package.json`, `SETUP_REPO.sh` (Node.js build support)

## [1.0.0] - 2026-03-02

### Initial Release
- Dual-stack PDF editor (PyQt5 Paint-style + CustomTkinter multi-tab)
- Drawing tools: pen, shapes, text, highlight
- OCR integration via ocrmypdf
- CLI mode for headless redaction and text extraction
- Page operations: merge, split, rotate, delete, insert
- PyInstaller packaging
