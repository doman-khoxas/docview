"""DocView right-click context menu — Cyber-Brutalist terminal-style popup.

Strict theme compliance: BG_ABYSS, BORDER_RED, TEXT_RED, HOVER_RED.
Courier font. Thick borders. Harsh aesthetic. All-caps labels.
"""
import tkinter as tk
from app.config import (
    BG_ABYSS, BORDER_RED, TEXT_RED,
    HOVER_RED, COLOR_DANGER
)


_MENU_FONT = ("Courier", 11)
_MENU_FONT_BOLD = ("Courier", 11, "bold")


class ContextMenu:
    """Harsh Cyber-Brutalist right-click popup menu."""

    def __init__(self, app_ref):
        self.app_ref = app_ref
        self._menu = tk.Menu(
            app_ref, tearoff=0,
            bg=BG_ABYSS,
            fg=TEXT_RED,
            activebackground=HOVER_RED,
            activeforeground=TEXT_RED,
            selectcolor=COLOR_DANGER,
            font=_MENU_FONT,
            borderwidth=2,
            relief="solid",
            activeborderwidth=0,
        )

        # --- Zoom section ---
        self._menu.add_command(label="  ZOOM +", command=self._zoom_in,
                               font=_MENU_FONT_BOLD)
        self._menu.add_command(label="  ZOOM -", command=self._zoom_out,
                               font=_MENU_FONT_BOLD)
        self._menu.add_command(label="  FIT WIDTH", command=self._fit_width,
                               font=_MENU_FONT_BOLD)
        self._add_separator()

        # --- Tool section ---
        self._menu.add_command(label="  HAND TOOL",
                               command=lambda: self._set_tool(None))
        self._menu.add_command(label="  SELECT",
                               command=lambda: self._set_tool("select"))
        self._menu.add_command(label="  HIGHLIGHT",
                               command=lambda: self._set_tool("highlight"))
        self._menu.add_command(label="  RECTANGLE",
                               command=lambda: self._set_tool("rect"))
        self._menu.add_command(label="  TEXT",
                               command=lambda: self._set_tool("text"))
        self._add_separator()

        # --- Page operations ---
        self._menu.add_command(label="  ROTATE PAGE", command=self._rotate)
        self._menu.add_command(label="  DELETE PAGE", command=self._delete_page,
                               foreground=COLOR_DANGER,
                               activeforeground=COLOR_DANGER)

    def _add_separator(self):
        """Add a themed separator line."""
        self._menu.add_separator(background=BORDER_RED)

    def show(self, x: int, y: int):
        try:
            self._menu.tk_popup(x, y)
        finally:
            self._menu.grab_release()

    def _zoom_in(self):
        self.app_ref.main_window.viewport.zoom_in()
        self.app_ref.update_status()

    def _zoom_out(self):
        self.app_ref.main_window.viewport.zoom_out()
        self.app_ref.update_status()

    def _fit_width(self):
        vp = self.app_ref.main_window.viewport
        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return
        from app.config import RENDER_DPI
        page = doc.get_page(vp.current_page)
        canvas_w = vp.canvas.winfo_width()
        page_w = page.rect.width * (RENDER_DPI / 72)
        if page_w > 0:
            vp.set_zoom(canvas_w / page_w)
            self.app_ref.update_status()

    def _set_tool(self, tool_name):
        if tool_name is None:
            self.app_ref.active_tool = None
            self.app_ref.main_window.toolbar.highlight_tool(None)
        else:
            self.app_ref.set_tool(tool_name)

    def _rotate(self):
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
