#!/usr/bin/env python3
"""
DocNotes — Note-taking app with Vault/Notebook/Section/Page hierarchy.

Usage:
  python docnotes/docnotes.py                    # Launch GUI
  python docnotes/docnotes.py --vault ~/mynotes  # Use specific vault
"""
import sys
import os
import argparse

# Ensure project root is on path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from docnotes.config import APP_NAME, APP_VERSION, DEFAULT_VAULT_ROOT


def main():
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} v{APP_VERSION} — Note-taking with Notebook/Section/Page hierarchy")
    parser.add_argument("--vault", default=DEFAULT_VAULT_ROOT,
                        help=f"Vault directory (default: {DEFAULT_VAULT_ROOT})")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {APP_VERSION}")
    args = parser.parse_args()

    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        print("ERROR: PyQt5 required. Run: pip install PyQt5")
        sys.exit(1)

    from docnotes.core.vault import Vault
    from docnotes.ui.app import DocNotesApp
    from docnotes.ui.main_window import MainWindow

    # Initialize vault
    vault = Vault(args.vault)
    vault.ensure_exists()
    vault.scan()

    # Launch app
    app = DocNotesApp(sys.argv)
    window = MainWindow(vault, app)
    app.setup_tray(window)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
