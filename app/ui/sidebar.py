"""Collapsible left panel with 3 tabs: Thumbnails, Bookmarks/TOC, Annotations."""
import tkinter as tk
import customtkinter as ctk
from PIL import ImageTk
from app.config import (
    SIDEBAR_WIDTH, THUMBNAIL_WIDTH, ACTIVE_THUMBNAIL_BORDER,
    THUMBNAIL_BORDER, LAZY_THUMBNAIL_THRESHOLD,
)
from app.core.pdf_renderer import render_thumbnail


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(parent, width=SIDEBAR_WIDTH, fg_color=("gray92", "gray17"))
        self.app_ref = app_ref
        self.pack_propagate(False)
        self._visible = True
        self._active_tab = "thumbnails"

        # tab selector row
        self._tab_row = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self._tab_row.pack(fill="x", padx=2, pady=(4, 0))
        self._tab_row.pack_propagate(False)

        self._tab_btns: dict[str, ctk.CTkButton] = {}
        for label, key in [("Pages", "thumbnails"), ("TOC", "bookmarks"), ("Notes", "annotations")]:
            btn = ctk.CTkButton(
                self._tab_row, text=label, width=60, height=24,
                font=ctk.CTkFont(size=11),
                fg_color="transparent", hover_color=("gray80", "gray30"),
                command=lambda k=key: self._switch_tab(k))
            btn.pack(side="left", padx=1)
            self._tab_btns[key] = btn

        # content area
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=2, pady=2)

        # -- thumbnails panel --
        self._thumb_frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        self._thumbnails: list[tuple] = []  # (PhotoImage | None, frame_widget)
        self._active_page = 0

        # -- bookmarks panel --
        self._bm_frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")

        # -- annotations panel --
        self._ann_frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")

        self._switch_tab("thumbnails")

    # ------------------------------------------------------------------
    # visibility
    # ------------------------------------------------------------------

    def toggle(self):
        if self._visible:
            self.pack_forget()
            self._visible = False
        else:
            # re-pack as the first child on the left
            self.pack(side="left", fill="y")
            # move to front so it appears leftmost
            children = self.master.pack_slaves()
            if len(children) > 1:
                self.pack_configure(before=children[1])
            self._visible = True

    @property
    def is_visible(self) -> bool:
        return self._visible

    # ------------------------------------------------------------------
    # tab switching
    # ------------------------------------------------------------------

    def _switch_tab(self, key: str):
        self._active_tab = key
        for k, btn in self._tab_btns.items():
            btn.configure(fg_color=("gray78", "gray30") if k == key else "transparent")

        # hide all, show selected
        for f in (self._thumb_frame, self._bm_frame, self._ann_frame):
            f.pack_forget()

        if key == "thumbnails":
            self._thumb_frame.pack(fill="both", expand=True)
        elif key == "bookmarks":
            self._bm_frame.pack(fill="both", expand=True)
        elif key == "annotations":
            self._ann_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # thumbnails
    # ------------------------------------------------------------------

    def refresh(self):
        """Rebuild thumbnails for the current document."""
        self._refresh_thumbnails()
        self._refresh_bookmarks()
        self._refresh_annotations()

    def _refresh_thumbnails(self):
        for _, widget in self._thumbnails:
            widget.destroy()
        self._thumbnails.clear()

        doc = self._get_doc()
        if not doc or not doc.is_open:
            return

        page_count = doc.page_count
        lazy = page_count > LAZY_THUMBNAIL_THRESHOLD

        for i in range(page_count):
            frame = ctk.CTkFrame(self._thumb_frame, fg_color="transparent")
            frame.pack(pady=3, padx=5)

            if not lazy:
                self._render_thumb(i, frame)
            else:
                ph = ctk.CTkLabel(frame, text=f"Page {i + 1}",
                                  width=THUMBNAIL_WIDTH, height=40)
                ph.pack()
                ph.bind("<Button-1>",
                        lambda e, pn=i, f=frame, p=ph: self._lazy_load(pn, f, p))
                self._thumbnails.append((None, frame))

        if not lazy:
            self.highlight_page(self._active_page)

    def _render_thumb(self, page_num: int, frame: ctk.CTkFrame):
        doc = self._get_doc()
        if not doc:
            return
        page = doc.get_page(page_num)
        img = render_thumbnail(page, THUMBNAIL_WIDTH)
        photo = ImageTk.PhotoImage(img)

        lbl = tk.Label(frame, image=photo, bd=2, relief="solid",
                       highlightthickness=2, highlightbackground=THUMBNAIL_BORDER)
        lbl.image = photo
        lbl.pack()

        num_label = ctk.CTkLabel(frame, text=f"{page_num + 1}",
                                 font=ctk.CTkFont(size=10))
        num_label.pack()

        lbl.bind("<Button-1>", lambda e, pn=page_num: self._on_thumb_click(pn))

        if len(self._thumbnails) > page_num:
            self._thumbnails[page_num] = (photo, frame)
        else:
            self._thumbnails.append((photo, frame))

    def _lazy_load(self, page_num, frame, placeholder):
        placeholder.destroy()
        self._render_thumb(page_num, frame)
        self._on_thumb_click(page_num)

    def _on_thumb_click(self, page_num: int):
        self._active_page = page_num
        self.app_ref.main_window.viewport.go_to_page(page_num)
        self.highlight_page(page_num)

    def highlight_page(self, page_num: int):
        self._active_page = page_num
        for i, (_, frame) in enumerate(self._thumbnails):
            for child in frame.winfo_children():
                if isinstance(child, tk.Label):
                    color = ACTIVE_THUMBNAIL_BORDER if i == page_num else THUMBNAIL_BORDER
                    child.configure(highlightbackground=color)

    # ------------------------------------------------------------------
    # bookmarks / TOC
    # ------------------------------------------------------------------

    def _refresh_bookmarks(self):
        for w in self._bm_frame.winfo_children():
            w.destroy()

        doc = self._get_doc()
        if not doc or not doc.is_open:
            return

        try:
            toc = doc.doc.get_toc()
        except Exception:
            toc = []

        if not toc:
            ctk.CTkLabel(self._bm_frame, text="No bookmarks",
                         font=ctk.CTkFont(size=11)).pack(pady=10)
            return

        for level, title, page_num in toc:
            indent = "  " * (level - 1)
            btn = ctk.CTkButton(
                self._bm_frame,
                text=f"{indent}{title}",
                anchor="w", fg_color="transparent",
                hover_color=("gray80", "gray30"),
                font=ctk.CTkFont(size=11),
                command=lambda pn=page_num - 1: self._on_thumb_click(max(0, pn)))
            btn.pack(fill="x", padx=2, pady=1)

    # ------------------------------------------------------------------
    # annotations list
    # ------------------------------------------------------------------

    def _refresh_annotations(self):
        for w in self._ann_frame.winfo_children():
            w.destroy()

        doc = self._get_doc()
        if not doc or not doc.is_open:
            return

        all_annots = doc.get_all_pending_annotations()
        if not all_annots:
            ctk.CTkLabel(self._ann_frame, text="No annotations",
                         font=ctk.CTkFont(size=11)).pack(pady=10)
            return

        for page_num in sorted(all_annots.keys()):
            for annot in all_annots[page_num]:
                label = type(annot).__name__.replace("Annotation", "")
                btn = ctk.CTkButton(
                    self._ann_frame,
                    text=f"Pg {page_num + 1}: {label}",
                    anchor="w", fg_color="transparent",
                    hover_color=("gray80", "gray30"),
                    font=ctk.CTkFont(size=11),
                    command=lambda pn=page_num: self._on_thumb_click(pn))
                btn.pack(fill="x", padx=2, pady=1)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _get_doc(self):
        return getattr(self.app_ref, 'pdf_doc', None)
