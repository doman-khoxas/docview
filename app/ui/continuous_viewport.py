"""Continuous vertical-scroll viewport — all pages stacked with gaps/shadows, lazy render."""
import tkinter as tk
from collections import OrderedDict
from PIL import ImageTk
from app.config import (
    ZOOM_DEFAULT, ZOOM_MIN, ZOOM_MAX, ZOOM_STEP, CANVAS_BG,
    PAGE_GAP, PAGE_SHADOW_OFFSET, PAGE_SHADOW_COLOR,
    OVERSCAN_PX, PAGE_CACHE_SIZE, RENDER_DPI,
)
from app.core.pdf_renderer import render_page, get_render_scale, pdf_to_canvas_coords


class _PageCanvasProxy:
    """Wraps tk.Canvas so page-relative coords from tools are offset
    to absolute canvas coords for drawing, while everything else is
    delegated transparently."""

    def __init__(self, canvas: tk.Canvas):
        self._canvas = canvas
        self._xoff = 0.0
        self._yoff = 0.0

    def set_page_offset(self, x_offset: float, y_offset: float):
        self._xoff = x_offset
        self._yoff = y_offset

    # --- drawing primitives used by tools ---
    def create_rectangle(self, x1, y1, x2, y2, **kw):
        return self._canvas.create_rectangle(
            x1 + self._xoff, y1 + self._yoff,
            x2 + self._xoff, y2 + self._yoff, **kw)

    def create_oval(self, x1, y1, x2, y2, **kw):
        return self._canvas.create_oval(
            x1 + self._xoff, y1 + self._yoff,
            x2 + self._xoff, y2 + self._yoff, **kw)

    def create_line(self, *args, **kw):
        coords = list(args)
        for i in range(0, len(coords), 2):
            coords[i] += self._xoff
            if i + 1 < len(coords):
                coords[i + 1] += self._yoff
        return self._canvas.create_line(*coords, **kw)

    def create_text(self, x, y, **kw):
        return self._canvas.create_text(
            x + self._xoff, y + self._yoff, **kw)

    def create_polygon(self, *args, **kw):
        coords = list(args)
        for i in range(0, len(coords), 2):
            coords[i] += self._xoff
            if i + 1 < len(coords):
                coords[i + 1] += self._yoff
        return self._canvas.create_polygon(*coords, **kw)

    def delete(self, *args):
        return self._canvas.delete(*args)

    def configure(self, **kw):
        return self._canvas.configure(**kw)

    config = configure

    def __getattr__(self, name):
        return getattr(self._canvas, name)


class ContinuousViewport(tk.Frame):
    def __init__(self, parent, app_ref):
        super().__init__(parent, bg=CANVAS_BG)
        self.app_ref = app_ref
        self.zoom = ZOOM_DEFAULT
        self.current_page = 0

        # page layout: [(y_offset, page_width_px, page_height_px), ...]
        self._page_layout: list[tuple[float, float, float]] = []
        # LRU cache: page_num -> (PhotoImage, PIL.Image)
        self._page_cache: OrderedDict = OrderedDict()
        # set of page_nums currently drawn on canvas
        self._drawn_pages: set[int] = set()
        # keep refs to PhotoImages so they aren't GC'd
        self._photo_refs: dict[int, ImageTk.PhotoImage] = {}

        # --- widgets ---
        self.canvas = tk.Canvas(self, bg=CANVAS_BG, highlightthickness=0)
        self._proxy = _PageCanvasProxy(self.canvas)
        self.v_scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._on_yscroll)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- bindings ---
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<ButtonPress-3>", self._on_right_click)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

        self._pending_render = False
        self._pending_configure = None  # debounce handle for configure events
        self._pending_zoom = None       # debounce handle for zoom operations
        self._last_canvas_w = 0         # track width to skip no-op configures

    # ------------------------------------------------------------------
    # public API (called by tools, toolbar, app)
    # ------------------------------------------------------------------

    @property
    def page_canvas_proxy(self):
        return self._proxy

    def load_document(self):
        """Call after opening / switching a document."""
        self._page_cache.clear()
        self._drawn_pages.clear()
        self._photo_refs.clear()
        self._compute_layout()
        self.canvas.delete("all")
        self._render_visible_pages()

    def render_current_page(self):
        """Compatibility shim: tools call this after annotation changes."""
        pn = self.current_page
        # remove old canvas items for this page
        self.canvas.delete(f"page_{pn}")
        self.canvas.delete(f"shadow_{pn}")
        self.canvas.delete(f"annot_{pn}")
        self._page_cache.pop(pn, None)
        self._drawn_pages.discard(pn)
        self._photo_refs.pop(pn, None)
        self._render_visible_pages()
        self.app_ref.update_status()

    def go_to_page(self, page_num: int):
        doc = self._get_doc()
        if not doc or not doc.is_open:
            return
        page_num = max(0, min(page_num, doc.page_count - 1))
        self.current_page = page_num
        if self._page_layout and page_num < len(self._page_layout):
            y_off = self._page_layout[page_num][0]
            total = self._total_height()
            if total > 0:
                self.canvas.yview_moveto(max(0, y_off - PAGE_GAP) / total)
        self._render_visible_pages()
        self.app_ref.update_status()

    def next_page(self):
        self.go_to_page(self.current_page + 1)

    def prev_page(self):
        self.go_to_page(self.current_page - 1)

    def set_zoom(self, zoom: float):
        old_zoom = self.zoom
        self.zoom = max(ZOOM_MIN, min(zoom, ZOOM_MAX))
        if self.zoom != old_zoom:
            # Debounce zoom: defer the expensive re-render until scroll stops
            if self._pending_zoom is not None:
                self.after_cancel(self._pending_zoom)
            self._pending_zoom = self.after(100, self._apply_zoom)

    def _apply_zoom(self):
        """Deferred zoom execution — runs once after rapid scroll stops."""
        self._pending_zoom = None
        self._page_cache.clear()
        self._drawn_pages.clear()
        self._photo_refs.clear()
        self._compute_layout()
        self.canvas.delete("all")
        self.go_to_page(self.current_page)

    def zoom_in(self):
        self.set_zoom(self.zoom + ZOOM_STEP)

    def zoom_out(self):
        self.set_zoom(self.zoom - ZOOM_STEP)

    def get_scroll_y(self) -> float:
        vals = self.canvas.yview()
        return vals[0] if vals else 0.0

    def set_scroll_y(self, frac: float):
        self.canvas.yview_moveto(frac)
        self._render_visible_pages()

    def canvas_to_page_coords(self, cx: float, cy: float):
        """Canvas-absolute coords -> (page_num, pdf_x, pdf_y) or (None,0,0)."""
        canvas_w = self.canvas.winfo_width()
        from app.core.pdf_renderer import canvas_to_pdf_coords
        for pn, (y_off, pw, ph) in enumerate(self._page_layout):
            x_off = (canvas_w - pw) / 2
            if y_off <= cy <= y_off + ph and x_off <= cx <= x_off + pw:
                page_cx = cx - x_off
                page_cy = cy - y_off
                pdf_x, pdf_y = canvas_to_pdf_coords(page_cx, page_cy, self.zoom)
                return pn, pdf_x, pdf_y
        return None, 0.0, 0.0

    # ------------------------------------------------------------------
    # layout
    # ------------------------------------------------------------------

    def _get_doc(self):
        return getattr(self.app_ref, 'pdf_doc', None)

    def _compute_layout(self):
        doc = self._get_doc()
        if not doc or not doc.is_open:
            self._page_layout = []
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
            return

        scale = get_render_scale(self.zoom)
        y = PAGE_GAP
        layout = []
        for i in range(doc.page_count):
            page = doc.get_page(i)
            pw = page.rect.width * scale
            ph = page.rect.height * scale
            layout.append((y, pw, ph))
            y += ph + PAGE_GAP

        self._page_layout = layout
        canvas_w = max(self.canvas.winfo_width(), 1)
        self.canvas.configure(scrollregion=(0, 0, canvas_w, y))

    def _total_height(self) -> float:
        if not self._page_layout:
            return 0
        last_y, _, last_h = self._page_layout[-1]
        return last_y + last_h + PAGE_GAP

    # ------------------------------------------------------------------
    # rendering
    # ------------------------------------------------------------------

    def _render_visible_pages(self):
        doc = self._get_doc()
        if not doc or not doc.is_open or not self._page_layout:
            return

        canvas_h = self.canvas.winfo_height()
        if canvas_h <= 1:
            return

        y_top = self.canvas.canvasy(0)
        y_bot = y_top + canvas_h
        y_top_os = y_top - OVERSCAN_PX
        y_bot_os = y_bot + OVERSCAN_PX
        canvas_w = self.canvas.winfo_width()

        visible = set()
        for pn, (y_off, pw, ph) in enumerate(self._page_layout):
            if y_off + ph >= y_top_os and y_off <= y_bot_os:
                visible.add(pn)

        # remove pages no longer visible
        for pn in list(self._drawn_pages):
            if pn not in visible:
                self.canvas.delete(f"page_{pn}")
                self.canvas.delete(f"shadow_{pn}")
                self.canvas.delete(f"annot_{pn}")
                self._drawn_pages.discard(pn)
                self._photo_refs.pop(pn, None)

        # draw newly visible pages
        for pn in visible:
            if pn not in self._drawn_pages:
                self._draw_page(pn, canvas_w)

        # update current page based on center of visible area
        center_y = (y_top + y_bot) / 2
        for pn, (y_off, pw, ph) in enumerate(self._page_layout):
            if y_off <= center_y <= y_off + ph:
                if self.current_page != pn:
                    self.current_page = pn
                break

    def _draw_page(self, page_num: int, canvas_w: float):
        doc = self._get_doc()
        if not doc or page_num >= doc.page_count:
            return

        y_off, pw, ph = self._page_layout[page_num]
        x_off = (canvas_w - pw) / 2

        # shadow
        self.canvas.create_rectangle(
            x_off + PAGE_SHADOW_OFFSET, y_off + PAGE_SHADOW_OFFSET,
            x_off + pw + PAGE_SHADOW_OFFSET, y_off + ph + PAGE_SHADOW_OFFSET,
            fill=PAGE_SHADOW_COLOR, outline="", tags=f"shadow_{page_num}")

        # get or render page image
        if page_num in self._page_cache:
            self._page_cache.move_to_end(page_num)
            pil_img = self._page_cache[page_num]
        else:
            page = doc.get_page(page_num)
            pil_img = render_page(page, self.zoom)
            self._page_cache[page_num] = pil_img
            # evict oldest if over limit, but never evict drawn pages
            while len(self._page_cache) > PAGE_CACHE_SIZE:
                # find first evictable (not currently drawn on canvas)
                evicted_pn = None
                for pn_key in self._page_cache:
                    if pn_key not in self._drawn_pages:
                        evicted_pn = pn_key
                        break
                if evicted_pn is None:
                    break  # all cached pages are drawn; can't evict
                del self._page_cache[evicted_pn]
                self._photo_refs.pop(evicted_pn, None)

        photo = ImageTk.PhotoImage(pil_img)
        self._photo_refs[page_num] = photo

        self.canvas.create_image(
            x_off, y_off, anchor="nw", image=photo, tags=f"page_{page_num}")

        # draw pending annotations for this page
        self._draw_page_annotations(page_num, x_off, y_off)

        self._drawn_pages.add(page_num)

    def _draw_page_annotations(self, page_num: int, x_off: float, y_off: float):
        from app.core.annotation_model import (
            RectAnnotation, CircleAnnotation, LineAnnotation,
            HighlightAnnotation, FreetextAnnotation, InkAnnotation,
            RedactAnnotation, ImageAnnotation,
        )
        doc = self._get_doc()
        if not doc:
            return
        annotations = doc.get_pending_annotations(page_num)
        scale = get_render_scale(self.zoom)
        tag = f"annot_{page_num}"

        for annot in annotations:
            if isinstance(annot, RectAnnotation):
                fill = annot.fill_color if annot.fill_color else ""
                self.canvas.create_rectangle(
                    x_off + annot.x0 * scale, y_off + annot.y0 * scale,
                    x_off + annot.x1 * scale, y_off + annot.y1 * scale,
                    outline=annot.color, fill=fill, width=annot.border_width, tags=tag)
            elif isinstance(annot, CircleAnnotation):
                fill = annot.fill_color if annot.fill_color else ""
                self.canvas.create_oval(
                    x_off + annot.x0 * scale, y_off + annot.y0 * scale,
                    x_off + annot.x1 * scale, y_off + annot.y1 * scale,
                    outline=annot.color, fill=fill, width=annot.border_width, tags=tag)
            elif isinstance(annot, LineAnnotation):
                self.canvas.create_line(
                    x_off + annot.x0 * scale, y_off + annot.y0 * scale,
                    x_off + annot.x1 * scale, y_off + annot.y1 * scale,
                    fill=annot.color, width=annot.border_width, tags=tag)
            elif isinstance(annot, HighlightAnnotation):
                for quad in annot.quads:
                    pts = [
                        x_off + quad.ul.x * scale, y_off + quad.ul.y * scale,
                        x_off + quad.ur.x * scale, y_off + quad.ur.y * scale,
                        x_off + quad.lr.x * scale, y_off + quad.lr.y * scale,
                        x_off + quad.ll.x * scale, y_off + quad.ll.y * scale,
                    ]
                    self.canvas.create_polygon(
                        pts, fill=annot.color, outline="",
                        stipple="gray50", tags=tag)
            elif isinstance(annot, FreetextAnnotation):
                self.canvas.create_text(
                    x_off + annot.x * scale, y_off + annot.y * scale,
                    text=annot.text, anchor="nw", fill=annot.text_color,
                    font=("Helvetica", max(8, int(annot.font_size * self.zoom))),
                    tags=tag)
            elif isinstance(annot, InkAnnotation):
                if len(annot.points) >= 2:
                    coords = []
                    for px, py in annot.points:
                        coords.extend([x_off + px * scale, y_off + py * scale])
                    self.canvas.create_line(
                        *coords, fill=annot.color,
                        width=annot.border_width, smooth=True, tags=tag)
            elif isinstance(annot, RedactAnnotation):
                # Red striped overlay for pending redaction
                self.canvas.create_rectangle(
                    x_off + annot.x0 * scale, y_off + annot.y0 * scale,
                    x_off + annot.x1 * scale, y_off + annot.y1 * scale,
                    fill="#ED4245", outline="#ED4245", width=2,
                    stipple="gray50", tags=tag)
            elif isinstance(annot, ImageAnnotation):
                # Show image preview or placeholder
                ix0 = x_off + annot.x0 * scale
                iy0 = y_off + annot.y0 * scale
                ix1 = x_off + annot.x1 * scale
                iy1 = y_off + annot.y1 * scale
                try:
                    from PIL import Image
                    img = Image.open(annot.image_path)
                    w = max(1, int(ix1 - ix0))
                    h = max(1, int(iy1 - iy0))
                    img = img.resize((w, h), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    # store ref to prevent GC
                    if not hasattr(self, '_annot_photo_refs'):
                        self._annot_photo_refs = {}
                    key = f"img_{page_num}_{id(annot)}"
                    self._annot_photo_refs[key] = photo
                    self.canvas.create_image(
                        ix0, iy0, anchor="nw", image=photo, tags=tag)
                except Exception:
                    # Fallback: dashed rect with [IMG] label
                    self.canvas.create_rectangle(
                        ix0, iy0, ix1, iy1,
                        outline="#4A9EFF", width=2, dash=(6, 3), tags=tag)
                    self.canvas.create_text(
                        (ix0 + ix1) / 2, (iy0 + iy1) / 2,
                        text="[IMG]", fill="#4A9EFF",
                        font=("Segoe UI", 10), tags=tag)

    # ------------------------------------------------------------------
    # event handlers
    # ------------------------------------------------------------------

    def _on_yscroll(self, *args):
        self.v_scroll.set(*args)
        self._schedule_render()

    def _schedule_render(self):
        if not self._pending_render:
            self._pending_render = True
            self.after(16, self._do_render)

    def _do_render(self):
        self._pending_render = False
        self._render_visible_pages()

    def _on_configure(self, event):
        # Debounce configure events — only re-render after resizing stops
        new_w = self.canvas.winfo_width()
        new_h = self.canvas.winfo_height()
        if new_w == self._last_canvas_w and new_h == getattr(self, '_last_canvas_h', 0):
            return  # no actual size change
        self._last_canvas_w = new_w
        self._last_canvas_h = new_h
        if self._pending_configure is not None:
            self.after_cancel(self._pending_configure)
        self._pending_configure = self.after(80, self._do_configure)

    def _do_configure(self):
        self._pending_configure = None
        self._compute_layout()
        self._drawn_pages.clear()
        self._photo_refs.clear()
        self.canvas.delete("all")
        self._render_visible_pages()

    def _on_mousewheel(self, event):
        # Check if Ctrl is held (state bit 0x0004 on Windows/Linux)
        if event.state & 0x0004:
            # Ctrl+Scroll = zoom (fallback for systems where Control-MouseWheel doesn't fire)
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            self.app_ref.update_status()
            return "break"
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _on_ctrl_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        self.app_ref.update_status()
        return "break"

    def _page_x_offset(self, page_num: int) -> float:
        if page_num >= len(self._page_layout):
            return 0
        _, pw, _ = self._page_layout[page_num]
        return (self.canvas.winfo_width() - pw) / 2

    def _on_press(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        # determine page
        page_num = self._page_at(cy)
        if page_num is not None:
            self.current_page = page_num

        # hand tool: use scan for smooth panning
        from app.tools.hand_tool import HandTool
        tool = self.app_ref.active_tool
        if tool is None or isinstance(tool, HandTool):
            self.canvas.scan_mark(event.x, event.y)
            self.canvas.configure(cursor="fleur")
            return

        if page_num is None:
            return

        # set proxy offset so tool temp-drawing lands at correct canvas position
        x_off = self._page_x_offset(page_num)
        y_off = self._page_layout[page_num][0]
        self._proxy.set_page_offset(x_off, y_off)

        # pass page-relative canvas coords to tool
        tool.on_press(cx - x_off, cy - y_off)

    def _on_drag(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        from app.tools.hand_tool import HandTool
        tool = self.app_ref.active_tool
        if tool is None or isinstance(tool, HandTool):
            self.canvas.scan_dragto(event.x, event.y, gain=1)
            self._schedule_render()
            return

        if tool and self.current_page < len(self._page_layout):
            x_off = self._page_x_offset(self.current_page)
            y_off = self._page_layout[self.current_page][0]
            tool.on_drag(cx - x_off, cy - y_off)

    def _on_release(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        from app.tools.hand_tool import HandTool
        tool = self.app_ref.active_tool
        if tool is None or isinstance(tool, HandTool):
            self.canvas.configure(cursor="hand2")
            return

        if tool and self.current_page < len(self._page_layout):
            x_off = self._page_x_offset(self.current_page)
            y_off = self._page_layout[self.current_page][0]
            tool.on_release(cx - x_off, cy - y_off)

    def _on_right_click(self, event):
        if hasattr(self.app_ref, 'main_window'):
            mw = self.app_ref.main_window
            if hasattr(mw, 'context_menu'):
                mw.context_menu.show(event.x_root, event.y_root)

    def _on_double_click(self, event):
        """Double-click to edit existing FreetextAnnotation."""
        from app.core.annotation_model import FreetextAnnotation
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        page_num = self._page_at(cy)
        if page_num is None:
            return

        doc = self._get_doc()
        if not doc or not doc.is_open:
            return

        x_off = self._page_x_offset(page_num)
        y_off = self._page_layout[page_num][0]
        scale = get_render_scale(self.zoom)

        # find FreetextAnnotation under cursor
        px = (cx - x_off) / scale
        py = (cy - y_off) / scale

        annotations = doc.get_pending_annotations(page_num)
        for annot in reversed(annotations):
            if isinstance(annot, FreetextAnnotation):
                if abs(px - annot.x) < 30 and abs(py - annot.y) < 20:
                    # open edit dialog
                    from app.ui.dialogs.text_input_dialog import TextInputDialog
                    dialog = TextInputDialog(self.app_ref)
                    dialog._entry.insert(0, annot.text)
                    dialog._entry.select_range(0, "end")
                    dialog.title("Edit Text")
                    self.app_ref.wait_window(dialog)
                    if dialog.result:
                        annot.text = dialog.result
                        doc.modified = True
                        self.render_current_page()
                    return "break"

    def _page_at(self, cy: float) -> int | None:
        for pn, (y_off, pw, ph) in enumerate(self._page_layout):
            if y_off <= cy <= y_off + ph:
                return pn
        return None

    # ------------------------------------------------------------------
    # search highlighting
    # ------------------------------------------------------------------

    def highlight_search_results(self, results: list[tuple[int, list]]):
        """results = [(page_num, [fitz.Rect, ...]), ...]"""
        self.canvas.delete("search_hl")
        scale = get_render_scale(self.zoom)
        canvas_w = self.canvas.winfo_width()
        for page_num, rects in results:
            if page_num >= len(self._page_layout):
                continue
            y_off, pw, ph = self._page_layout[page_num]
            x_off = (canvas_w - pw) / 2
            for r in rects:
                self.canvas.create_rectangle(
                    x_off + r.x0 * scale, y_off + r.y0 * scale,
                    x_off + r.x1 * scale, y_off + r.y1 * scale,
                    fill="#FFD700", outline="", stipple="gray50",
                    tags="search_hl")

    def clear_search_highlights(self):
        self.canvas.delete("search_hl")
