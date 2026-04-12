"""DocNotes configuration constants."""
from pathlib import Path

APP_NAME = "DocNotes"
APP_VERSION = "1.0.0"

# Vault
DEFAULT_VAULT_ROOT = str(Path.home() / ".docnotes")
VAULT_META_FILE = "vault.yaml"
NOTEBOOK_META_FILE = "_notebook.yaml"
SECTION_META_FILE = "_section.yaml"
STICKY_DIR_NAME = "_sticky"

# Window
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
MIN_WIDTH = 800
MIN_HEIGHT = 500

# Panel widths
NOTEBOOK_TREE_WIDTH = 220
NOTE_LIST_WIDTH = 260

# Note defaults
NOTE_AUTOSAVE_MS = 500
DEFAULT_NOTE_TITLE = "Untitled"

# Sticky notes
STICKY_WIDTH = 280
STICKY_HEIGHT = 280

# Notebook colors (for tree icons)
NOTEBOOK_COLORS = [
    "#007acc",  # blue
    "#4ec9b0",  # teal
    "#dcdcaa",  # yellow
    "#ce9178",  # orange
    "#c586c0",  # purple
    "#d16969",  # red
    "#608b4e",  # green
    "#9cdcfe",  # light blue
]
