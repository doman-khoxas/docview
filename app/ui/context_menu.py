"""Right-click context menu on the viewport canvas."""
import tkinter as tk


class ContextMenu:
    def __init__(self, app_ref):
        self.app_ref = app_ref
        self._menu = tk.Menu(app_ref, tearoff=0)

        self._menu.add_command(label="Zoom In", command=self._zoom_in)
        self._menu.add_command(label="Zoom Out", command=self._zoom_out)
        self._menu.add_command(label="Fit Width", command=self._fit_width)
        self._menu.add_separator()
        self._menu.add_command(label="Hand Tool", command=lambda: self._set_tool(None))
        self._menu.add_command(label="Select", command=lambda: self._set_tool("select"))
        self._menu.add_command(label="Highlight", command=lambda: self._set_tool("highlight"))
        self._menu.add_command(label="Rectangle", command=lambda: self._set_tool("rect"))
        self._menu.add_command(label="Text", command=lambda: self._set_tool("text"))
        self._menu.add_separator()
        self._menu.add_command(label="Rotate Page", command=self._rotate)
        self._menu.add_command(label="Delete Page", command=self._delete_page)

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
