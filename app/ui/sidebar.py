"""DocView sidebar — page thumbnails, table of contents, annotation list."""
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import ImageTk
from app.config import (
    SIDEBAR_WIDTH, THUMBNAIL_WIDTH, ACTIVE_THUMBNAIL_BORDER,
    THUMBNAIL_BORDER, LAZY_THUMBNAIL_THRESHOLD,
    BG_PANEL, BG_ABYSS, BORDER_RED, TEXT_RED, HOVER_RED, ACTIVE_RED, TEXT_MUTED, CORNER_RADIUS,
    ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, BG_SURFACE, BG_ACTIVE, ACCENT_MUTED, BORDER_SUBTLE
)
from app.core.pdf_renderer import render_thumbnail


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        # Apply the harsh structural styling
        super().__init__(
            parent, width=SIDEBAR_WIDTH,
            fg_color=BG_PANEL,
            border_color=BORDER_SUBTLE,
            border_width=1,
            corner_radius=CORNER_RADIUS
        )
        self.app_ref = app_ref
        self.pack_propagate(False)
        self._visible = True
        self._active_tab = "thumbnails"

        # ── Row 1: Tab Selector ──
        self._tab_row = ctk.CTkFrame(self, fg_color=BG_ABYSS, height=35, corner_radius=CORNER_RADIUS)
        self._tab_row.pack(fill="x", padx=0, pady=0)
        self._tab_row.pack_propagate(False)

        self._tab_btns: dict[str, ctk.CTkButton] = {}
        for label, key in [("PAGES", "thumbnails"), ("TOC", "bookmarks"), ("NOTES", "annotations")]:
            btn = ctk.CTkButton(
                self._tab_row, text=label, width=60, height=35,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="transparent",
                text_color=TEXT_SECONDARY,
                hover_color=HOVER_RED,
                corner_radius=CORNER_RADIUS,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(side="left", fill="both", expand=True)
            self._tab_btns[key] = btn

        # ── Content Area ──
        self._content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=CORNER_RADIUS)
        self._content.pack(fill="both", expand=True, padx=2, pady=2)

        self._thumb_frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent", corner_radius=CORNER_RADIUS)
        self._thumbnails: list[tuple] = []  
        self._active_page = 0

        self._bm_frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent", corner_radius=CORNER_RADIUS)
        self._ann_frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent", corner_radius=CORNER_RADIUS)

        # Right-click context menu for page thumbnails
        self._page_context_menu = tk.Menu(self, tearoff=0)
        self._page_context_menu.add_command(label="Extract Page...", command=self._extract_page)
        self._page_context_menu.add_command(label="Extract Pages...", command=self._extract_page_range)
        self._page_context_menu.add_separator()
        self._page_context_menu.add_command(label="Rotate Page", command=self._rotate_page)
        self._page_context_menu.add_command(label="Insert Blank Page After", command=self._insert_blank_after)
        self._page_context_menu.add_separator()
        self._page_context_menu.add_command(label="Delete Page", command=self._delete_page)
        self._right_click_page = 0

        self._switch_tab("thumbnails")

    def toggle(self):
        if self._visible:
            self.pack_forget()
            self._visible = False
        else:
            self.pack(side="left", fill="y")
            children = self.master.pack_slaves()
            if len(children) > 1:
                self.pack_configure(before=children[1])
            self._visible = True

    @property
    def is_visible(self) -> bool:
        return self._visible

    def _switch_tab(self, key: str):
        self._active_tab = key
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.configure(fg_color=ACCENT_MUTED, text_color=ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)

        for f in (self._thumb_frame, self._bm_frame, self._ann_frame):
            f.pack_forget()

        if key == "thumbnails":
            self._thumb_frame.pack(fill="both", expand=True)
        elif key == "bookmarks":
            self._bm_frame.pack(fill="both", expand=True)
        elif key == "annotations":
            self._ann_frame.pack(fill="both", expand=True)

    def refresh(self):
        self._refresh_thumbnails()
        # Defer non-visible tab refreshes to avoid blocking the main thread
        self.after_idle(self._refresh_bookmarks)
        self.after_idle(self._refresh_annotations)

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
                ph = ctk.CTkLabel(frame, text=f"Page {i + 1}", width=THUMBNAIL_WIDTH, height=40, text_color=TEXT_SECONDARY, font=ctk.CTkFont(family="Segoe UI"))
                ph.pack()
                ph.bind("<Button-1>", lambda e, pn=i, f=frame, p=ph: self._lazy_load(pn, f, p))
                self._thumbnails.append((None, frame))

        if not lazy:
            self.highlight_page(self._active_page)

    def _render_thumb(self, page_num: int, frame: ctk.CTkFrame):
        doc = self._get_doc()
        if not doc: return
        page = doc.get_page(page_num)
        img = render_thumbnail(page, THUMBNAIL_WIDTH)
        photo = ImageTk.PhotoImage(img)

        # Apply brutalist borders to thumbnails
        lbl = tk.Label(frame, image=photo, bd=0, relief="flat", highlightthickness=2, highlightbackground=BORDER_SUBTLE, bg=BG_PANEL)
        lbl.image = photo  # type: ignore
        lbl.pack()

        num_label = ctk.CTkLabel(frame, text=f"{page_num + 1}", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=TEXT_SECONDARY)
        num_label.pack()

        lbl.bind("<Button-1>", lambda e, pn=page_num: self._on_thumb_click(pn))
        lbl.bind("<Button-3>", lambda e, pn=page_num: self._on_thumb_right_click(e, pn))

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

    def _refresh_bookmarks(self):
        for w in self._bm_frame.winfo_children(): w.destroy()
        doc = self._get_doc()
        if not doc or not doc.is_open: return

        try:
            toc = doc.doc.get_toc()
        except Exception:
            toc = []

        if not toc:
            ctk.CTkLabel(self._bm_frame, text="NO BOOKMARKS", text_color=TEXT_MUTED, font=ctk.CTkFont(family="Segoe UI", size=11)).pack(pady=10)
            return

        for level, title, page_num in toc:
            indent = "  " * (level - 1)
            btn = ctk.CTkButton(
                self._bm_frame, text=f"{indent}> {title}", anchor="w", fg_color="transparent", text_color=TEXT_PRIMARY,
                hover_color=HOVER_RED, corner_radius=0, font=ctk.CTkFont(family="Segoe UI", size=11),
                command=lambda pn=page_num - 1: self._on_thumb_click(max(0, pn)))
            btn.pack(fill="x", padx=2, pady=1)

    def _refresh_annotations(self):
        for w in self._ann_frame.winfo_children(): w.destroy()
        doc = self._get_doc()
        if not doc or not doc.is_open: return

        all_annots = doc.get_all_pending_annotations()
        if not all_annots:
            ctk.CTkLabel(self._ann_frame, text="NO ANNOTATIONS", text_color=TEXT_MUTED, font=ctk.CTkFont(family="Segoe UI", size=11)).pack(pady=10)
            return

        for page_num in sorted(all_annots.keys()):
            for annot in all_annots[page_num]:
                label = type(annot).__name__.replace("Annotation", "")
                btn = ctk.CTkButton(
                    self._ann_frame, text=f"PG {page_num + 1} : {label.upper()}", anchor="w", fg_color="transparent", text_color=TEXT_PRIMARY,
                    hover_color=HOVER_RED, corner_radius=0, font=ctk.CTkFont(family="Segoe UI", size=11),
                    command=lambda pn=page_num: self._on_thumb_click(pn))
                btn.pack(fill="x", padx=2, pady=1)

    def _on_thumb_right_click(self, event, page_num: int):
        self._right_click_page = page_num
        self._on_thumb_click(page_num)
        try:
            self._page_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._page_context_menu.grab_release()

    def _extract_page(self):
        """Extract the right-clicked page to a new PDF file."""
        import fitz
        doc = self._get_doc()
        if not doc or not doc.is_open:
            return
        page_num = self._right_click_page
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"{doc.file_name.replace('.pdf', '')}_page{page_num + 1}.pdf"
        )
        if path:
            try:
                new_doc = fitz.open()
                new_doc.insert_pdf(doc.doc, from_page=page_num, to_page=page_num)
                new_doc.save(path)
                new_doc.close()
                messagebox.showinfo("Extracted", f"Page {page_num + 1} saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract page:\n{e}")

    def _extract_page_range(self):
        """Extract a range of pages via a simple dialog."""
        import fitz
        doc = self._get_doc()
        if not doc or not doc.is_open:
            return

        # Simple range dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Extract Pages")
        dialog.geometry("300x160")
        dialog.resizable(False, False)
        dialog.transient(self.app_ref)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Pages (1-{doc.page_count}):",
                     font=ctk.CTkFont(family="Segoe UI", size=12)).pack(pady=(15, 5))

        row = ctk.CTkFrame(dialog, fg_color="transparent")
        row.pack(pady=5)
        from_var = ctk.StringVar(value=str(self._right_click_page + 1))
        to_var = ctk.StringVar(value=str(self._right_click_page + 1))
        ctk.CTkEntry(row, textvariable=from_var, width=60).pack(side="left", padx=5)
        ctk.CTkLabel(row, text="to").pack(side="left")
        ctk.CTkEntry(row, textvariable=to_var, width=60).pack(side="left", padx=5)

        def do_extract():
            try:
                f = max(1, int(from_var.get()))
                t = min(doc.page_count, int(to_var.get()))
            except ValueError:
                return
            dialog.destroy()
            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"{doc.file_name.replace('.pdf', '')}_p{f}-{t}.pdf"
            )
            if path:
                try:
                    new_doc = fitz.open()
                    new_doc.insert_pdf(doc.doc, from_page=f - 1, to_page=t - 1)
                    new_doc.save(path)
                    new_doc.close()
                    messagebox.showinfo("Extracted", f"Pages {f}-{t} saved to:\n{path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to extract pages:\n{e}")

        ctk.CTkButton(dialog, text="Extract", command=do_extract).pack(pady=10)

    def _rotate_page(self):
        from app.core.page_operations import rotate_page
        doc = self._get_doc()
        if not doc or not doc.is_open:
            return
        rotate_page(doc.doc, self._right_click_page)
        doc.modified = True
        self.app_ref.main_window.viewport.load_document()
        self.refresh()

    def _insert_blank_after(self):
        from app.core.page_operations import insert_blank_page
        doc = self._get_doc()
        if not doc or not doc.is_open:
            return
        insert_blank_page(doc.doc, self._right_click_page + 1)
        doc.modified = True
        self.app_ref.main_window.viewport.load_document()
        self.refresh()

    def _delete_page(self):
        doc = self._get_doc()
        if not doc or not doc.is_open or doc.page_count <= 1:
            return
        page_num = self._right_click_page
        confirm = messagebox.askyesno(
            "Delete Page", f"Delete page {page_num + 1}? This cannot be undone.")
        if not confirm:
            return
        from app.core.page_operations import delete_pages
        delete_pages(doc.doc, [page_num])
        doc.modified = True
        self.app_ref.main_window.viewport.load_document()
        self.refresh()

    def _get_doc(self):
        return getattr(self.app_ref, 'pdf_doc', None)