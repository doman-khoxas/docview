# Build & Install — `build.py`, `install.py`, `main.py`

Build, packaging, and installation infrastructure for distributing DocView as a standalone Windows application.

---

## `build.py` — PyInstaller Build Script

**Purpose:** Create a standalone `.exe` via PyInstaller.

**Key Steps:**
1. Generate application icon if missing (`assets/generate_icon.py`)
2. Run PyInstaller with `--onefile --windowed` flags
3. Include assets directory as data
4. Output to `dist/DocView.exe`

**Dependencies:** `pyinstaller`, `Pillow` (for icon generation)

---

## `install.py` — Windows File Association Installer

**Purpose:** Register DocView as the default handler for `.pdf` files on Windows.

**Features:**
- Creates Windows Registry entries for file association
- Sets up `Open With` context menu integration
- Registers application in `App Paths`
- Creates Start Menu shortcut
- Handles UAC elevation for admin registry writes

**Error Handling:**
- `FileNotFoundError` — graceful skip if registry keys don't exist
- `PermissionError` — reports need for admin privileges
- All operations are individually try/caught to allow partial success

---

## `assets/generate_icon.py` — Icon Generator

**Purpose:** Generates `docview.ico` and `docview.png` application icons programmatically using Pillow.

---

## `main.py` — Entry Point

See [app.md](app.md) for full documentation.

**Key points:**
- Handles both script execution and PyInstaller frozen bundle
- CLI argument: `docview.exe myfile.pdf` opens the file
- Crash logging writes to `crashlog.txt` alongside the executable
- Structured logging initialized before any app code runs

---

## Distribution

| File | Purpose |
|------|---------|
| `dist/DocView.exe` | Standalone executable |
| `crashlog.txt` | Crash log (created at runtime if needed) |
| `~/.pdf_editor/` | User data directory |
| `~/.pdf_editor/recent_files.json` | Recent files list |
| `~/.pdf_editor/logs/docview.log` | Structured application log |
