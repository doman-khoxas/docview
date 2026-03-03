# DocView Changelog

All notable changes to DocView are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [2.0.0] - 2026-03-03

### Added
- Complete UI overhaul: Cyber Brutalist dark theme with layered gray depth system
- Ribbon-style toolbar inspired by PDFgear / Windows 11 Paint with 4 tabs (Home, Edit, Page, Tools)
- Compound `_RibbonButton` widget with large symbols (20pt) and labels (10pt)
- Multi-document tabbed interface with CustomTkinter
- Continuous viewport with page gap, shadows, and overscan rendering
- Page management tab: New PDF, Insert Pages, Insert Blank, Extract, Delete, Rotate Left/Right
- PDFgear-style Extract Pages dialog with range selection (Selected/All/Custom), extract modes (one PDF / separate), delete-after-extraction option
- Document overview panel with grid thumbnails, multi-select (click-to-toggle), Select All
- Drag-and-drop page reorder in overview panel with visual drop indicators
- Page range input field (eg. 1,8,10-12) with Apply button
- PDF compression: image downscaling via Pillow + garbage collection + deflate
- Metadata stripping (OPSEC): removes Title, Author, Subject, Keywords, Creator, Producer, dates, XMP
- Digital signature support: PFX/P12 certificate signing via endesive, visible stamp fallback
- Redaction tool with apply/clear workflow
- Annotation tools: freehand, highlight, rectangle, circle, line, text, image
- Image annotation rendering in viewport with PIL resize and fallback placeholder
- Double-click text editing on FreeText annotations
- Properties panel for annotation styling (color, opacity, font size, border width)
- Right-click context menu on sidebar thumbnails (Extract, Rotate, Insert Blank, Delete)
- Search panel (Ctrl+F) with highlight navigation
- Undo/Redo system for annotations (Ctrl+Z / Ctrl+Y)
- Print support (Ctrl+P) using OS print system
- Sidebar toggle (Ctrl+B) with hamburger button in status bar
- Keyboard navigation: arrows, Page Up/Down, Home/End
- Zoom controls: Ctrl+/-, fit-to-width, zoom percentage display
- Save confirmation dialog before overwrite
- Welcome screen for empty state
- Crash logging to crashlog.txt with timestamp, Python version, platform, traceback
- Version management system with semantic versioning
- Update utility (update.py) for version bumps, changelog, and release prep
- PyInstaller build system with icon generation, assets inclusion
- Build batch file (docview-build.bat) for one-click packaging

### Changed
- Migrated from PyQt5 monolith (docview.py) to modular CustomTkinter architecture
- Color system: professional dark palette with BG_DEEP → BG_PANEL → BG_SURFACE → BG_HOVER → BG_ACTIVE layers
- Borders brightened for panel contrast (BORDER_DEFAULT #44464B, BORDER_SUBTLE #35373B)
- Page shadows deepened (PAGE_SHADOW_COLOR #0D0E10)
- Toolbar symbols use BMP Unicode only (no astral plane emoji) for Tkinter compatibility

### Removed
- Old PyQt5 monolith (docview.py, 1700+ lines)
- PyQt5 and ocrmypdf dependencies
- Stale files: package.json, package-lock.json, SETUP_REPO.sh, DocView.spec, CODE_REVIEW.md

### Fixed
- CTkFrame transparency ValueError: replaced `border_color="transparent"` with proper color values
- Unicode escape syntax error: replaced JS-style `\u{1F4C2}` with Python `\U0001F4C2`
- Toolbar button symbols too tiny: refactored from single CTkButton to compound _RibbonButton
- Tab bar border color crash when opening multiple documents

## [1.0.0] - 2026-02-15

### Added
- Initial PDF viewer with PyQt5
- Basic annotation support
- Single-document viewing
