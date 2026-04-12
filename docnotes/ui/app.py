"""DocNotes QApplication with dark theme and system tray."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from docnotes.config import APP_NAME
from app.ui.theme import apply_dark_palette, STYLESHEET


def _find_docnotes_icon() -> QIcon:
    """Load the DocNotes-specific icon (teal sticky note)."""
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                     "assets", "docnotes_icon.ico"),
        os.path.join(getattr(sys, '_MEIPASS', ''), "assets", "docnotes_icon.ico"),
        os.path.join(os.path.dirname(sys.executable), "assets", "docnotes_icon.ico"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return QIcon(path)
    # Fallback to png
    for path in candidates:
        png = path.replace(".ico", "_256.png")
        if os.path.exists(png):
            return QIcon(png)
    # Last fallback: DocView icon
    from app.ui.app import _find_icon
    return _find_icon()


class DocNotesApp(QApplication):
    def __init__(self, argv=None):
        super().__init__(argv or sys.argv)
        self.setApplicationName(APP_NAME)
        self.setOrganizationName("Operator Systems")
        self.setStyle("Fusion")
        apply_dark_palette(self)
        self.setStyleSheet(STYLESHEET)

        self._icon = _find_docnotes_icon()
        self.setWindowIcon(self._icon)

        self._tray: QSystemTrayIcon | None = None
        self._main_window = None

    def setup_tray(self, main_window):
        self._main_window = main_window
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self._tray = QSystemTrayIcon(self._icon, self)
        self._tray.setToolTip(APP_NAME)

        menu = QMenu()
        menu.addAction("Show DocNotes", self._show_main)
        menu.addSeparator()
        menu.addAction("New Sticky Note", self._new_sticky)
        menu.addSeparator()
        menu.addAction("Quit", self._quit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

    def _show_main(self):
        if self._main_window:
            self._main_window.show()
            self._main_window.raise_()
            self._main_window.activateWindow()

    def _new_sticky(self):
        if self._main_window and hasattr(self._main_window, 'create_sticky'):
            self._main_window.create_sticky()

    def _quit(self):
        if self._main_window:
            self._main_window.close()
        self.quit()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_main()
