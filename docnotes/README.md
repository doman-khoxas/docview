# DocNotes

**Note-taking app with Vault/Notebook/Section/Page hierarchy**

Built by Operator Systems // BLACK TECH WIZARD

---

## Overview

DocNotes is a desktop note-taking app that replaces OneNote. It stores notes as plain Markdown files with YAML frontmatter in a folder-based vault structure. Includes desktop sticky notes with section assignment, OneNote `.one` file import, and a markdown editor with live preview.

**Version 1.0.0**

## Features

### Vault Hierarchy
- **Vault** (root directory) → **Notebook** (folder) → **Section** (subfolder) → **Page** (.md file)
- All metadata in YAML frontmatter — no proprietary formats
- Obsidian-compatible `.md` files

### Three-Panel UI
- **Left**: Notebook/Section tree with colored icons
- **Center**: Note list with search filter, pin support, timestamps
- **Right**: Markdown editor with Preview / Split / Edit modes

### Sticky Notes
- Floating desktop sticky notes via system tray
- Right-click system tray → New Sticky Note
- 6 colors: yellow, blue, green, pink, orange, purple
- **Section assignment**: assign a sticky to any Notebook/Section
- **Convert to Page**: promote a sticky to a full note in the assigned section
- Auto-save with 500ms debounce
- Position and size restored on restart

### Markdown Editor
- Syntax highlighting (headers, bold, italic, code, wikilinks, tags)
- Line numbers with current-line highlighting
- Live HTML preview with split pane
- `[[Wikilink]]` support — click to navigate
- Word count and line count

### OneNote Import
- Imports raw `.one` binary files (ONESTORE format)
- Imports HTML exports (`.htm`, `.html`)
- Preserves folder structure as Notebook → Section hierarchy
- Handles nested sub-sections (e.g., UConn/Fall 2024/ACCT-5121)
- File → Import OneNote → select folder → done

### CRUD Operations
- Create / rename / delete notebooks, sections, pages
- Pin notes to top of list
- Search across all notes (title + content)
- Right-click context menus throughout

### System Tray
- New Sticky Note
- Quick Capture
- Show / Hide all stickies
- Quit

## Quick Start

```bash
# From the docview project root
pip install -r requirements.txt

# Launch DocNotes
python docnotes/docnotes.py

# Use a custom vault location
python docnotes/docnotes.py --vault C:\path\to\my\vault

# Version
python docnotes/docnotes.py --version
```

Default vault: `~/.docnotes/`

## Build Executable

**Important**: Run all build commands from the **project root** (`docview/`), not from `docnotes/`.

### Portable Executable (single .exe)

```bash
cd C:\Users\gt8le\Operator\Documents\Code\GitHub\docview
pip install pyinstaller
python build_docnotes.py
```

Output: `dist/DocNotes.exe`

### Directory Bundle (faster startup)

```bash
python build_docnotes.py --onedir
```

Output: `dist/DocNotes/DocNotes.exe`

### Clean + Build

```bash
python build_docnotes.py --clean
```

### Windows Installer

After building with `--onedir`, use Inno Setup to create a proper installer.
See the DocView `installer.iss` as a template — change `MyAppName` to `DocNotes`.

## Vault Structure

```
~/.docnotes/
├── vault.yaml                    # Vault metadata
├── Personal/                     # Notebook
│   ├── _notebook.yaml            # Notebook config (name, color)
│   ├── Journal/                  # Section
│   │   ├── _section.yaml         # Section config
│   │   └── 2026-04-12.md         # Page
│   └── Ideas/
│       └── project-alpha.md
├── Work/
│   ├── _notebook.yaml
│   └── Meetings/
│       └── standup-notes.md
└── _sticky/                      # Sticky notes
    ├── abc123.md
    └── def456.md
```

### Page Frontmatter

```yaml
---
title: Meeting Notes
created: 2026-04-12T10:30:00
modified: 2026-04-12T11:15:00
tags: [meeting, work]
pinned: false
---

Your markdown content here.
```

### Sticky Note Frontmatter

```yaml
---
title: Quick thought
sticky: true
section: Work/Meetings
color: yellow
x: 100
y: 200
width: 280
height: 280
created: 2026-04-12T10:30:00
modified: 2026-04-12T10:35:00
---

Remember to follow up on the budget review.
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Page |
| Ctrl+Shift+N | New Notebook |
| Ctrl+Alt+N | New Sticky Note |
| Ctrl+Shift+F | Search All Notes |
| F5 | Refresh Vault |
| Ctrl+Q | Quit |

## Requirements

- Python 3.9+
- PyQt5 >= 5.15
- PyMuPDF >= 1.23
- markdown >= 3.5
- pyyaml >= 6.0
- Pillow >= 10.0

## License

MIT

---

*Operator Systems // BLACK TECH WIZARD Build*
