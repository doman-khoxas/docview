"""Assembles all panels: toolbar, tab_bar, sidebar, viewport, search, status bar."""
import customtkinter as ctk
from app.ui.toolbar import Toolbar
from app.ui.tab_bar import TabBar
from app.ui.continuous_viewport import ContinuousViewport
from app.ui.sidebar import Sidebar
from app.ui.properties_panel import PropertiesPanel
from app.ui.status_bar import StatusBar
from app.ui.welcome_screen import WelcomeScreen
from app.ui.search_panel import SearchPanel
from app.ui.context_menu import ContextMenu
from app.ui.overview_panel import OverviewPanel
from app.config import BG_ABYSS, CORNER_RADIUS, BORDER_DEFAULT, BG_SURFACE


class MainWindow:
    def __init__(self, root, app_ref):
        self.root = root
        self.app_ref = app_ref

        # ── top: toolbar ──
        self.toolbar = Toolbar(root, app_ref)
        self.toolbar.pack(fill="x", side="top")

        # ── top: tab bar (below toolbar) ──
        self.tab_bar = TabBar(root, app_ref)
        self.tab_bar.pack(fill="x", side="top")

        # ── bottom: status bar ──
        self.status_bar = StatusBar(root, app_ref)
        self.status_bar.pack(fill="x", side="bottom")

        # ── middle area: sidebar | viewport + search | properties ──
        # Enforce pure black background and sharp corners
        self.middle_frame = ctk.CTkFrame(root, fg_color=BG_ABYSS, corner_radius=CORNER_RADIUS)
        self.middle_frame.pack(fill="both", expand=True)

        # sidebar (left)
        self.sidebar = Sidebar(self.middle_frame, app_ref)
        self.sidebar.pack(side="left", fill="y")

        # Vertical separator between sidebar and viewport
        self._sidebar_sep = ctk.CTkFrame(
            self.middle_frame, width=1, fg_color=BORDER_DEFAULT, corner_radius=0)
        self._sidebar_sep.pack(side="left", fill="y")

        # properties panel (right, starts hidden)
        self.properties_panel = PropertiesPanel(self.middle_frame, app_ref)
        # don't pack yet — shown on annotation tool select

        # center container for search + viewport/welcome
        self._center = ctk.CTkFrame(self.middle_frame, fg_color=BG_ABYSS, corner_radius=CORNER_RADIUS)
        self._center.pack(side="left", fill="both", expand=True)

        # search panel (above viewport, initially hidden)
        self.search_panel = SearchPanel(self._center, app_ref)

        # welcome screen
        self.welcome_screen = WelcomeScreen(self._center, app_ref)
        self.welcome_screen.pack(fill="both", expand=True)

        # continuous viewport (hidden until file opened)
        self.viewport = ContinuousViewport(self._center, app_ref)

        # context menu
        self.context_menu = ContextMenu(app_ref)

        # overview panel (floats over center area)
        self.overview_panel = OverviewPanel(self._center, app_ref)

        self._doc_open = False

    def show_document(self):
        """Switch from welcome screen to document view."""
        if not self._doc_open:
            self.welcome_screen.pack_forget()
            self.viewport.pack(fill="both", expand=True)
            self._doc_open = True
        self.viewport.load_document()
        self.tab_bar.refresh()
        self.sidebar.refresh()

    def show_welcome(self):
        """Switch back to welcome screen (all tabs closed)."""
        if self._doc_open:
            self.viewport.pack_forget()
            self.welcome_screen.pack(fill="both", expand=True)
            self.welcome_screen.refresh_recent()
            self._doc_open = False
        self.tab_bar.refresh()