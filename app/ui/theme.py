"""Dark theme palette and stylesheet for DocView."""
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt


# ── Color constants ──
BG_PRIMARY = "#1e1e1e"
BG_SURFACE = "#252526"
BG_ELEVATED = "#2d2d2d"
BG_HOVER = "#2a2d2e"
BG_SELECTED = "#37373d"
BG_INPUT = "#3c3c3c"

BORDER = "#3c3c3c"
BORDER_FOCUS = "#007acc"

TEXT_PRIMARY = "#cccccc"
TEXT_SECONDARY = "#858585"
TEXT_DISABLED = "#5a5a5a"

ACCENT = "#007acc"
ACCENT_HOVER = "#1a8ad4"
ACCENT_PRESSED = "#005a9e"

SUCCESS = "#4ec9b0"
WARNING = "#dcdcaa"
ERROR = "#f44747"
INFO = "#9cdcfe"

# Sticky note colors
STICKY_YELLOW = "#fff9c4"
STICKY_BLUE = "#bbdefb"
STICKY_GREEN = "#c8e6c9"
STICKY_PINK = "#f8bbd0"
STICKY_ORANGE = "#ffe0b2"
STICKY_PURPLE = "#e1bee7"

STICKY_COLORS = {
    "yellow": STICKY_YELLOW,
    "blue": STICKY_BLUE,
    "green": STICKY_GREEN,
    "pink": STICKY_PINK,
    "orange": STICKY_ORANGE,
    "purple": STICKY_PURPLE,
}

# Canvas
CANVAS_BG = "#1a1a1a"
PAGE_SHADOW = "#0a0a0a"


def apply_dark_palette(app: QApplication):
    """Apply VS Code-style dark palette to the application."""
    palette = QPalette()

    palette.setColor(QPalette.Window, QColor(BG_PRIMARY))
    palette.setColor(QPalette.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Base, QColor(BG_SURFACE))
    palette.setColor(QPalette.AlternateBase, QColor(BG_ELEVATED))
    palette.setColor(QPalette.ToolTipBase, QColor(BG_ELEVATED))
    palette.setColor(QPalette.ToolTipText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Button, QColor(BG_SURFACE))
    palette.setColor(QPalette.ButtonText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.BrightText, QColor(ERROR))
    palette.setColor(QPalette.Link, QColor(ACCENT))
    palette.setColor(QPalette.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))

    palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(TEXT_DISABLED))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(TEXT_DISABLED))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(TEXT_DISABLED))

    app.setPalette(palette)


STYLESHEET = f"""
QMainWindow {{
    background-color: {BG_PRIMARY};
}}

QMenuBar {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border-bottom: 1px solid {BORDER};
    padding: 2px;
}}
QMenuBar::item:selected {{
    background-color: {BG_HOVER};
}}
QMenu {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    padding: 4px;
}}
QMenu::item:selected {{
    background-color: {ACCENT};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 4px 8px;
}}

QToolBar {{
    background-color: {BG_SURFACE};
    border-bottom: 1px solid {BORDER};
    spacing: 2px;
    padding: 2px 4px;
}}
QToolBar::separator {{
    width: 1px;
    background: {BORDER};
    margin: 4px 2px;
}}
QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 4px 6px;
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}
QToolButton:hover {{
    background-color: {BG_HOVER};
    border-color: {BORDER};
}}
QToolButton:pressed, QToolButton:checked {{
    background-color: {BG_SELECTED};
    border-color: {ACCENT};
}}

QTabBar {{
    background-color: {BG_PRIMARY};
    border: none;
}}
QTabBar::tab {{
    background-color: {BG_SURFACE};
    color: {TEXT_SECONDARY};
    padding: 6px 16px;
    margin-right: 1px;
    border: none;
    border-bottom: 2px solid transparent;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    color: {TEXT_PRIMARY};
    background-color: {BG_PRIMARY};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover:!selected {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}
QTabBar::close-button {{
    image: none;
    subcontrol-position: right;
}}

QDockWidget {{
    color: {TEXT_PRIMARY};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}
QDockWidget::title {{
    background-color: {BG_SURFACE};
    padding: 6px;
    border-bottom: 1px solid {BORDER};
    text-align: left;
}}

QScrollBar:vertical {{
    background: {BG_PRIMARY};
    width: 12px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BG_INPUT};
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_SECONDARY};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {BG_PRIMARY};
    height: 12px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {BG_INPUT};
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {TEXT_SECONDARY};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QStatusBar {{
    background-color: {ACCENT};
    color: #ffffff;
    font-size: 12px;
    padding: 0 8px;
}}
QStatusBar::item {{
    border: none;
}}

QLineEdit, QSpinBox, QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 4px 8px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}

QPushButton {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 3px;
    padding: 5px 16px;
    min-width: 60px;
}}
QPushButton:hover {{
    background-color: {BG_HOVER};
    border-color: {ACCENT};
}}
QPushButton:pressed {{
    background-color: {BG_SELECTED};
}}
QPushButton:default {{
    background-color: {ACCENT};
    border-color: {ACCENT};
    color: #ffffff;
}}
QPushButton:default:hover {{
    background-color: {ACCENT_HOVER};
}}

QTreeView, QListWidget, QTableWidget {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    alternate-background-color: {BG_ELEVATED};
    selection-background-color: {BG_SELECTED};
}}
QTreeView::item:hover, QListWidget::item:hover {{
    background-color: {BG_HOVER};
}}
QTreeView::item:selected, QListWidget::item:selected {{
    background-color: {BG_SELECTED};
}}
QHeaderView::section {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    padding: 4px;
}}

QSplitter::handle {{
    background-color: {BORDER};
}}
QSplitter::handle:horizontal {{
    width: 2px;
}}
QSplitter::handle:vertical {{
    height: 2px;
}}

QToolTip {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    padding: 4px;
}}

QProgressBar {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 3px;
    text-align: center;
    color: {TEXT_PRIMARY};
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 3px;
}}

QSlider::groove:horizontal {{
    background: {BG_INPUT};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: {ACCENT_HOVER};
}}
"""
