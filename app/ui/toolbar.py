"""Ribbon-style toolbar with category tabs: Home, View, Comment, Edit."""
import customtkinter as ctk


_TAB_CATEGORIES = ["Home", "View", "Comment", "Edit"]


class Toolbar(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(parent, fg_color=("gray92", "gray15"))
        self.app_ref = app_ref

        # ── Row 1: category tab buttons ──
        self._tab_row = ctk.CTkFrame(self, height=30, fg_color=("gray86", "gray20"))
        self._tab_row.pack(fill="x")
        self._tab_row.pack_propagate(False)

        # sidebar toggle (leftmost, always visible)
        self._sidebar_btn = ctk.CTkButton(
            self._tab_row, text="\u2630", width=32, height=26,
            font=ctk.CTkFont(size=15),
            fg_color="transparent", hover_color=("gray78", "gray30"),
            command=self._toggle_sidebar)
        self._sidebar_btn.pack(side="left", padx=(6, 10))

        self._cat_buttons: dict[str, ctk.CTkButton] = {}
        for cat in _TAB_CATEGORIES:
            btn = ctk.CTkButton(
                self._tab_row, text=cat, width=70, height=26,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent",
                hover_color=("gray78", "gray28"),
                corner_radius=4,
                command=lambda c=cat: self._switch_category(c))
            btn.pack(side="left", padx=2, pady=2)
            self._cat_buttons[cat] = btn

        # nav/zoom always-visible on the right of the tab row
        self._nav_frame = ctk.CTkFrame(self._tab_row, fg_color="transparent")
        self._nav_frame.pack(side="right", padx=6)

        ctk.CTkButton(self._nav_frame, text="\u25C0", width=26, height=24,
                      font=ctk.CTkFont(size=11),
                      fg_color="transparent", hover_color=("gray78", "gray30"),
                      command=self._prev_page).pack(side="left", padx=1)
        self.page_label = ctk.CTkLabel(self._nav_frame, text="0 / 0", width=55,
                                       font=ctk.CTkFont(size=11))
        self.page_label.pack(side="left")
        ctk.CTkButton(self._nav_frame, text="\u25B6", width=26, height=24,
                      font=ctk.CTkFont(size=11),
                      fg_color="transparent", hover_color=("gray78", "gray30"),
                      command=self._next_page).pack(side="left", padx=1)

        ctk.CTkFrame(self._nav_frame, width=1, height=20,
                     fg_color="gray50").pack(side="left", padx=6)

        ctk.CTkButton(self._nav_frame, text="\u2212", width=24, height=24,
                      font=ctk.CTkFont(size=12),
                      fg_color="transparent", hover_color=("gray78", "gray30"),
                      command=self._zoom_out).pack(side="left", padx=1)
        self.zoom_label = ctk.CTkLabel(self._nav_frame, text="100%", width=44,
                                       font=ctk.CTkFont(size=11))
        self.zoom_label.pack(side="left")
        ctk.CTkButton(self._nav_frame, text="+", width=24, height=24,
                      font=ctk.CTkFont(size=12),
                      fg_color="transparent", hover_color=("gray78", "gray30"),
                      command=self._zoom_in).pack(side="left", padx=1)

        # ── Row 2: ribbon content (changes per category) ──
        self._ribbon = ctk.CTkFrame(self, height=52, fg_color="transparent")
        self._ribbon.pack(fill="x")
        self._ribbon.pack_propagate(False)

        self._panels: dict[str, ctk.CTkFrame] = {}
        self._tool_buttons: dict[str | None, ctk.CTkButton] = {}

        self._build_home_panel()
        self._build_view_panel()
        self._build_comment_panel()
        self._build_edit_panel()

        self._active_cat = None
        self._switch_category("Home")

    # ------------------------------------------------------------------
    # panel builders
    # ------------------------------------------------------------------

    def _build_home_panel(self):
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Home"] = p

        # file group
        g1 = self._group(p, "File")
        for label, cmd in [("Open", self.app_ref.open_file_dialog),
                           ("Save", self.app_ref.save_file),
                           ("Save As", self.app_ref.save_file_as)]:
            ctk.CTkButton(g1, text=label, width=56, height=32,
                          font=ctk.CTkFont(size=11),
                          command=cmd).pack(side="left", padx=2)

        # quick tools
        g2 = self._group(p, "Tools")
        quick = [
            ("\u270B Hand", None),
            ("\u25E6 Select", "select"),
            ("\u2591 Highlight", "highlight"),
        ]
        for label, tool_name in quick:
            btn = ctk.CTkButton(
                g2, text=label, width=72, height=32,
                font=ctk.CTkFont(size=11),
                fg_color="transparent", hover_color=("gray78", "gray30"),
                command=lambda t=tool_name: self._set_tool(t))
            btn.pack(side="left", padx=2)
            self._tool_buttons[tool_name] = btn

    def _build_view_panel(self):
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["View"] = p

        g1 = self._group(p, "Zoom")
        ctk.CTkButton(g1, text="Zoom In", width=68, height=32,
                      font=ctk.CTkFont(size=11),
                      command=self._zoom_in).pack(side="left", padx=2)
        ctk.CTkButton(g1, text="Zoom Out", width=72, height=32,
                      font=ctk.CTkFont(size=11),
                      command=self._zoom_out).pack(side="left", padx=2)
        ctk.CTkButton(g1, text="Fit Width", width=72, height=32,
                      font=ctk.CTkFont(size=11),
                      command=self._zoom_fit).pack(side="left", padx=2)

        g2 = self._group(p, "Navigate")
        ctk.CTkButton(g2, text="Prev Page", width=76, height=32,
                      font=ctk.CTkFont(size=11),
                      command=self._prev_page).pack(side="left", padx=2)
        ctk.CTkButton(g2, text="Next Page", width=76, height=32,
                      font=ctk.CTkFont(size=11),
                      command=self._next_page).pack(side="left", padx=2)

        g3 = self._group(p, "Panels")
        ctk.CTkButton(g3, text="Sidebar", width=60, height=32,
                      font=ctk.CTkFont(size=11),
                      command=self._toggle_sidebar).pack(side="left", padx=2)
        ctk.CTkButton(g3, text="Search", width=60, height=32,
                      font=ctk.CTkFont(size=11),
                      command=self._toggle_search).pack(side="left", padx=2)

    def _build_comment_panel(self):
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Comment"] = p

        g1 = self._group(p, "Markup")
        tools = [
            ("\u270B Hand", None),
            ("\u25E6 Select", "select"),
            ("T Text", "text"),
            ("\u2591 Highlight", "highlight"),
        ]
        for label, tool_name in tools:
            btn = ctk.CTkButton(
                g1, text=label, width=72, height=32,
                font=ctk.CTkFont(size=11),
                fg_color="transparent", hover_color=("gray78", "gray30"),
                command=lambda t=tool_name: self._set_tool(t))
            btn.pack(side="left", padx=2)
            if tool_name not in self._tool_buttons:
                self._tool_buttons[tool_name] = btn

        g2 = self._group(p, "Shapes")
        shapes = [
            ("\u25AD Rect", "rect"),
            ("\u25EF Circle", "circle"),
            ("\u2571 Line", "line"),
            ("\u270E Draw", "freehand"),
        ]
        for label, tool_name in shapes:
            btn = ctk.CTkButton(
                g2, text=label, width=64, height=32,
                font=ctk.CTkFont(size=11),
                fg_color="transparent", hover_color=("gray78", "gray30"),
                command=lambda t=tool_name: self._set_tool(t))
            btn.pack(side="left", padx=2)
            if tool_name not in self._tool_buttons:
                self._tool_buttons[tool_name] = btn

    def _build_edit_panel(self):
        p = ctk.CTkFrame(self._ribbon, fg_color="transparent")
        self._panels["Edit"] = p

        g1 = self._group(p, "Pages")
        for label, cmd in [("Rotate", self._rotate_page),
                           ("Delete", self._delete_page),
                           ("Insert", self._insert_page)]:
            ctk.CTkButton(g1, text=label, width=60, height=32,
                          font=ctk.CTkFont(size=11),
                          command=cmd).pack(side="left", padx=2)

        g2 = self._group(p, "Document")
        for label, cmd in [("Merge", self._merge),
                           ("Split", self._split)]:
            ctk.CTkButton(g2, text=label, width=56, height=32,
                          font=ctk.CTkFont(size=11),
                          command=cmd).pack(side="left", padx=2)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _group(parent, title: str) -> ctk.CTkFrame:
        """Create a labelled tool group with a bottom title."""
        outer = ctk.CTkFrame(parent, fg_color="transparent")
        outer.pack(side="left", padx=(8, 4), fill="y")

        content = ctk.CTkFrame(outer, fg_color="transparent")
        content.pack(side="top", fill="x", expand=True, pady=(4, 0))

        ctk.CTkLabel(outer, text=title, font=ctk.CTkFont(size=9),
                     text_color=("gray50", "gray55")).pack(side="bottom")

        return content

    @staticmethod
    def _vsep(parent):
        ctk.CTkFrame(parent, width=1, height=40,
                     fg_color=("gray75", "gray35")).pack(side="left", padx=6, pady=4)

    def _switch_category(self, cat: str):
        if self._active_cat == cat:
            return
        self._active_cat = cat
        for c, btn in self._cat_buttons.items():
            if c == cat:
                btn.configure(fg_color=("white", "gray30"))
            else:
                btn.configure(fg_color="transparent")
        for c, panel in self._panels.items():
            if c == cat:
                panel.pack(fill="both", expand=True)
            else:
                panel.pack_forget()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def update_zoom_label(self, zoom: float):
        self.zoom_label.configure(text=f"{int(zoom * 100)}%")

    def update_page_label(self, current: int, total: int):
        self.page_label.configure(text=f"{current + 1} / {total}")

    def highlight_tool(self, tool_name: str | None):
        for name, btn in self._tool_buttons.items():
            if name == tool_name:
                btn.configure(fg_color=("gray68", "#1a5fb4"))
            else:
                btn.configure(fg_color="transparent")

    # ------------------------------------------------------------------
    # commands
    # ------------------------------------------------------------------

    def _set_tool(self, tool_name: str | None):
        if tool_name is None:
            self.app_ref.active_tool = None
            self.highlight_tool(None)
            self.app_ref.main_window.properties_panel.hide()
        else:
            self.app_ref.set_tool(tool_name)

    def _toggle_sidebar(self):
        mw = self.app_ref.main_window
        if hasattr(mw, 'sidebar'):
            mw.sidebar.toggle()

    def _toggle_search(self):
        sp = self.app_ref.main_window.search_panel
        if sp.is_open:
            sp.close()
        else:
            sp.open()

    def _zoom_in(self):
        vp = self.app_ref.main_window.viewport
        vp.zoom_in()
        self.app_ref.update_status()

    def _zoom_out(self):
        vp = self.app_ref.main_window.viewport
        vp.zoom_out()
        self.app_ref.update_status()

    def _zoom_fit(self):
        from app.config import RENDER_DPI
        vp = self.app_ref.main_window.viewport
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        page = doc.get_page(vp.current_page)
        canvas_w = vp.canvas.winfo_width()
        page_w = page.rect.width * (RENDER_DPI / 72)
        if page_w > 0:
            vp.set_zoom(canvas_w / page_w)
            self.app_ref.update_status()

    def _prev_page(self):
        self.app_ref.main_window.viewport.prev_page()

    def _next_page(self):
        self.app_ref.main_window.viewport.next_page()

    def _rotate_page(self):
        from app.core.page_operations import rotate_page
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        vp = self.app_ref.main_window.viewport
        rotate_page(doc.doc, vp.current_page)
        doc.modified = True
        vp.render_current_page()
        self.app_ref.main_window.sidebar.refresh()

    def _delete_page(self):
        from app.core.page_operations import delete_pages
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open or doc.page_count <= 1:
            return
        vp = self.app_ref.main_window.viewport
        page_num = vp.current_page
        delete_pages(doc.doc, [page_num])
        doc.modified = True
        vp.load_document()
        self.app_ref.main_window.sidebar.refresh()

    def _insert_page(self):
        from app.ui.dialogs.insert_page_dialog import InsertPageDialog
        dialog = InsertPageDialog(self.app_ref)
        dialog.grab_set()

    def _merge(self):
        from app.ui.dialogs.merge_dialog import MergeDialog
        dialog = MergeDialog(self.app_ref)
        dialog.grab_set()

    def _split(self):
        from app.ui.dialogs.split_dialog import SplitDialog
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        dialog = SplitDialog(self.app_ref)
        dialog.grab_set()
