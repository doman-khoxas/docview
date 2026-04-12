"""QApplication setup with dark theme and system tray."""
import sys
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from app.version import APP_NAME
from app.ui.theme import apply_dark_palette, STYLESHEET


def _find_icon() -> QIcon:
    """Load icon from assets directory, handling both dev and frozen (PyInstaller) paths."""
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "icon.ico"),
        os.path.join(getattr(sys, '_MEIPASS', ''), "assets", "icon.ico"),
        os.path.join(os.path.dirname(sys.executable), "assets", "icon.ico"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return QIcon(path)
    # Fallback: use .png variants
    for path in candidates:
        png = path.replace("icon.ico", "icon_256.png")
        if os.path.exists(png):
            return QIcon(png)
    return QIcon()


class DocViewApp(QApplication):
    def __init__(self, argv=None):
        super().__init__(argv or sys.argv)
        self.setApplicationName(APP_NAME)
        self.setOrganizationName("Operator Systems")
        self.setOrganizationDomain("operator.systems")
        self.setApplicationVersion("2.0.0")
        self.setStyle("Fusion")
        apply_dark_palette(self)
        self.setStyleSheet(STYLESHEET)

        self._icon = _find_icon()
        self.setWindowIcon(self._icon)

        self._tray: QSystemTrayIcon | None = None
        self._main_window = None

    def setup_tray(self, main_window):
        """Initialize system tray icon with context menu."""
        self._main_window = main_window

        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self._tray = QSystemTrayIcon(self._icon, self)
        self._tray.setToolTip(APP_NAME)

        menu = QMenu()
        show_action = QAction("Show DocView", menu)
        show_action.triggered.connect(self._show_main_window)
        menu.addAction(show_action)

        menu.addSeparator()

        new_note_action = QAction("New Sticky Note", menu)
        new_note_action.triggered.connect(self._new_sticky_note)
        menu.addAction(new_note_action)

        show_notes = QAction("Show All Notes", menu)
        show_notes.triggered.connect(self._show_all_notes)
        menu.addAction(show_notes)

        hide_notes = QAction("Hide All Notes", menu)
        hide_notes.triggered.connect(self._hide_all_notes)
        menu.addAction(hide_notes)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _show_main_window(self):
        if self._main_window:
            self._main_window.show()
            self._main_window.raise_()
            self._main_window.activateWindow()

    def _new_sticky_note(self):
        if self._main_window and hasattr(self._main_window, 'create_sticky_note'):
            self._main_window.create_sticky_note()

    def _show_all_notes(self):
        if self._main_window and hasattr(self._main_window, 'show_all_sticky_notes'):
            self._main_window.show_all_sticky_notes()

    def _hide_all_notes(self):
        if self._main_window and hasattr(self._main_window, 'hide_all_sticky_notes'):
            self._main_window.hide_all_sticky_notes()

    def _quit_app(self):
        if self._main_window:
            self._main_window.close()
        self.quit()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_main_window()
