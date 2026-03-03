"""Document overview — grid of all page thumbnails with multi-select and drag-drop reorder."""
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import ImageTk
from app.config import (
    BG_DEEP, BG_PANEL, ACCENT, ACCENT_MUTED, BORDER_SUBTLE, TEXT_PRIMARY,
    TEXT_SECONDARY, TEXT_MUTED, CORNER_RADIUS, BG_SURFACE, BG_ACTIVE,
    BORDER_DEFAULT, COLOR_DANGER, BG_HOVER
)
from app.core.pdf_renderer import render_thumbnail

_THUMB_SIZE = 160
_COLS = 4
_DRAG_THRESHOLD = 8   # pixels before drag starts
_RENDER_BATCH = 8     # pages per batch in grid rendering


class OverviewPanel(ctk.CTkFrame):
    """Full-screen grid overlay showing all pages with multi-select + drag-drop reorder."""

    def __init__(self, parent, app_ref):
        super().__init__(parent, fg_color=BG_DEEP, corner_radius=0)
        self.app_ref = app_ref
        self._visible = False
        self._extract_mode = False
        self._photo_refs: list = []
        self._selected_pages: set[int] = set()
        self._cell_frames: dict[int, ctk.CTkFrame] = {}
        self._page_widgets: dict[int, tk.Widget] = {}  # page_num -> clickable widget

        # Drag state
        self._drag_source: int | None = None
        self._drag_active = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drop_target: int | None = None
        self._drop_indicator: tk.Frame | None = None

        # Top bar
        self._top = ctk.CTkFrame(self, fg_color=BG_SURFACE, height=44, corner_radius=0)
        self._top.pack(fill="x")
        self._top.pack_propagate(False)

        self._title_lbl = ctk.CTkLabel(
            self._top, text="\u25A6  Document Overview",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        self._title_lbl.pack(side="left", padx=12)

        # Hint label for drag-drop
        self._hint_lbl = ctk.CTkLabel(
            self._top, text="Drag pages to reorder",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_MUTED
        )

        # Right side buttons
        self._close_btn = ctk.CTkButton(
            self._top, text="\u2715  Close", width=80, height=30,
            fg_color="transparent", hover_color=BG_ACTIVE,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4, command=self.hide
        )
        self._close_btn.pack(side="right", padx=8)

        # Extract mode buttons (hidden by default)
        self._extract_btn = ctk.CTkButton(
            self._top, text="\u2702  Extract Selected", width=140, height=30,
            fg_color=ACCENT, hover_color=ACCENT_MUTED,
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=4, command=self._do_extract
        )

        self._delete_btn = ctk.CTkButton(
            self._top, text="\u2717  Delete Selected", width=130, height=30,
            fg_color=COLOR_DANGER, hover_color="#C53030",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=4, command=self._do_delete
        )

        self._select_all_btn = ctk.CTkButton(
            self._top, text="Select All", width=80, height=30,
            fg_color="transparent", hover_color=BG_ACTIVE,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=4, command=self._select_all
        )

        self._count_lbl = ctk.CTkLabel(
            self._top, text="0 selected",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED
        )

        # Scrollable grid area
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_DEEP, corner_radius=0
        )
        self._scroll.pack(fill="both", expand=True, padx=8, pady=8)

    def show(self, extract_mode: bool = False):
        if self._visible and not extract_mode:
            self.hide()
            return
        self._visible = True
        self._extract_mode = extract_mode
        self._selected_pages.clear()

        # Update title and button visibility
        if extract_mode:
            self._title_lbl.configure(text="\u2702  Select Pages to Extract / Delete")
            self._extract_btn.pack(side="right", padx=4)
            self._delete_btn.pack(side="right", padx=4)
            self._select_all_btn.pack(side="right", padx=4)
            self._count_lbl.pack(side="right", padx=8)
            self._hint_lbl.pack(side="left", padx=8)
        else:
            self._title_lbl.configure(text="\u25A6  Document Overview")
            self._extract_btn.pack_forget()
            self._delete_btn.pack_forget()
            self._select_all_btn.pack_forget()
            self._count_lbl.pack_forget()
            self._hint_lbl.pack(side="left", padx=8)

        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self._render_grid()

    def hide(self):
        if not self._visible:
            return
        self._visible = False
        self._extract_mode = False
        self._selected_pages.clear()
        self._cancel_drag()
        # Hide action buttons
        self._extract_btn.pack_forget()
        self._delete_btn.pack_forget()
        self._select_all_btn.pack_forget()
        self._count_lbl.pack_forget()
        self._hint_lbl.pack_forget()
        self.place_forget()

    @property
    def is_open(self) -> bool:
        return self._visible

    def _render_grid(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._photo_refs.clear()
        self._cell_frames.clear()
        self._page_widgets.clear()

        doc = getattr(self.app_ref, 'pdf_doc', None)
        if not doc or not doc.is_open:
            return

        self._grid_doc = doc
        self._grid_total = doc.page_count
        self._grid_index = 0
        self._grid_row_frame = None
        # Render in batches of _BATCH_SIZE to keep UI responsive
        self._render_grid_batch()

    def _render_grid_batch(self):
        """Render a batch of grid cells, then schedule more via after_idle."""
        doc = getattr(self, '_grid_doc', None)
        if not doc or not doc.is_open:
            return
        total = self._grid_total
        end = min(self._grid_index + _RENDER_BATCH, total)

        for i in range(self._grid_index, end):
            col = i % _COLS
            if col == 0:
                self._grid_row_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
                self._grid_row_frame.pack(pady=4)

            cell = ctk.CTkFrame(self._grid_row_frame, fg_color=BG_PANEL,
                                corner_radius=CORNER_RADIUS,
                                border_width=2, border_color=BORDER_SUBTLE)
            cell.pack(side="left", padx=6, pady=4)
            self._cell_frames[i] = cell

            try:
                page = doc.get_page(i)
                img = render_thumbnail(page, _THUMB_SIZE)
                photo = ImageTk.PhotoImage(img)
                self._photo_refs.append(photo)

                lbl = tk.Label(cell, image=photo, bd=0, bg=BG_PANEL,
                               cursor="hand2")
                lbl.image = photo
                lbl.pack(padx=4, pady=(4, 0))
                self._page_widgets[i] = lbl

                # Bind mouse events for both click and drag
                self._bind_page_events(lbl, i)
            except Exception:
                placeholder = ctk.CTkLabel(cell, text=f"Page {i+1}",
                                           width=_THUMB_SIZE, height=80,
                                           text_color=TEXT_MUTED)
                placeholder.pack(padx=4, pady=4)
                self._page_widgets[i] = placeholder
                self._bind_page_events(placeholder, i)

            num = ctk.CTkLabel(
                cell, text=f"{i + 1}",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color=TEXT_SECONDARY
            )
            num.pack(pady=(0, 4))

        self._grid_index = end
        if self._grid_index < total:
            # Schedule next batch — lets the event loop breathe
            self.after(10, self._render_grid_batch)
        else:
            # All pages rendered, update selection visuals
            self._update_selection_visuals()

    def _bind_page_events(self, widget, page_num: int):
        """Bind press/drag/release for both click actions and drag-drop reorder."""
        widget.bind("<ButtonPress-1>", lambda e, pn=page_num: self._on_press(e, pn))
        widget.bind("<B1-Motion>", lambda e, pn=page_num: self._on_motion(e, pn))
        widget.bind("<ButtonRelease-1>", lambda e, pn=page_num: self._on_release(e, pn))

    def _on_press(self, event, page_num: int):
        """Record press position — drag starts after threshold."""
        self._drag_source = page_num
        self._drag_active = False
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root

    def _on_motion(self, event, page_num: int):
        """Check if drag threshold exceeded, then track drop target."""
        if self._drag_source is None:
            return
        dx = abs(event.x_root - self._drag_start_x)
        dy = abs(event.y_root - self._drag_start_y)
        if not self._drag_active and (dx > _DRAG_THRESHOLD or dy > _DRAG_THRESHOLD):
            self._drag_active = True
            # Visual feedback: highlight the source as being dragged
            src_cell = self._cell_frames.get(self._drag_source)
            if src_cell:
                src_cell.configure(fg_color=BG_HOVER, border_color=ACCENT)

        if self._drag_active:
            # Find which cell the cursor is over
            target = self._find_cell_at(event.x_root, event.y_root)
            if target != self._drop_target:
                self._drop_target = target
                self._update_drop_indicator()

    def _on_release(self, event, page_num: int):
        """If drag was active, reorder. Otherwise, perform click action."""
        if self._drag_active and self._drag_source is not None and self._drop_target is not None:
            if self._drag_source != self._drop_target:
                self._reorder_page(self._drag_source, self._drop_target)
            self._cancel_drag()
        else:
            # Normal click — select or navigate
            self._cancel_drag()
            if self._extract_mode:
                self._toggle_select(page_num)
            else:
                self._go_to_page(page_num)

    def _find_cell_at(self, x_root: int, y_root: int) -> int | None:
        """Find which page cell the cursor is over (by root coords)."""
        for pn, cell in self._cell_frames.items():
            try:
                cx = cell.winfo_rootx()
                cy = cell.winfo_rooty()
                cw = cell.winfo_width()
                ch = cell.winfo_height()
                if cx <= x_root <= cx + cw and cy <= y_root <= cy + ch:
                    return pn
            except Exception:
                continue
        return None

    def _update_drop_indicator(self):
        """Highlight the drop target cell."""
        for pn, cell in self._cell_frames.items():
            if pn == self._drop_target:
                cell.configure(border_color="#FFB020", border_width=3)
            elif pn == self._drag_source:
                cell.configure(border_color=ACCENT, border_width=2)
            elif pn in self._selected_pages:
                cell.configure(border_color=ACCENT, border_width=2)
            else:
                cell.configure(border_color=BORDER_SUBTLE, border_width=2)

    def _cancel_drag(self):
        """Reset all drag state and visuals."""
        self._drag_source = None
        self._drag_active = False
        self._drop_target = None
        # Restore normal visuals
        for pn, cell in self._cell_frames.items():
            if pn in self._selected_pages:
                cell.configure(border_color=ACCENT, fg_color=ACCENT_MUTED, border_width=2)
            else:
                cell.configure(border_color=BORDER_SUBTLE, fg_color=BG_PANEL, border_width=2)

    def _reorder_page(self, from_page: int, to_page: int):
        """Move a page from one position to another in the document."""
        doc = getattr(self.app_ref, 'pdf_doc', None)
        if not doc or not doc.is_open:
            return

        try:
            doc.doc.move_page(from_page, to_page)
            doc.modified = True

            # Update selection indices if needed
            if self._selected_pages:
                new_selected = set()
                for pn in self._selected_pages:
                    if pn == from_page:
                        new_selected.add(to_page if to_page < from_page else to_page - 1)
                    elif from_page < pn <= to_page:
                        new_selected.add(pn - 1)
                    elif to_page <= pn < from_page:
                        new_selected.add(pn + 1)
                    else:
                        new_selected.add(pn)
                self._selected_pages = new_selected

            # Re-render everything
            self._render_grid()
            self._update_selection_visuals()
            self.app_ref.main_window.viewport.load_document()
            self.app_ref.main_window.sidebar.refresh()
        except Exception as e:
            messagebox.showerror("Reorder Error", f"Failed to move page:\n{e}")

    # --- Selection ---
    def _toggle_select(self, page_num: int):
        if page_num in self._selected_pages:
            self._selected_pages.discard(page_num)
        else:
            self._selected_pages.add(page_num)
        self._update_selection_visuals()

    def _select_all(self):
        doc = getattr(self.app_ref, 'pdf_doc', None)
        if not doc or not doc.is_open:
            return
        if len(self._selected_pages) == doc.page_count:
            self._selected_pages.clear()
        else:
            self._selected_pages = set(range(doc.page_count))
        self._update_selection_visuals()

    def _update_selection_visuals(self):
        for pn, cell in self._cell_frames.items():
            if pn in self._selected_pages:
                cell.configure(border_color=ACCENT, fg_color=ACCENT_MUTED)
            else:
                cell.configure(border_color=BORDER_SUBTLE, fg_color=BG_PANEL)
        self._count_lbl.configure(text=f"{len(self._selected_pages)} selected")

    # --- Extract / Delete ---
    def _do_extract(self):
        doc = getattr(self.app_ref, 'pdf_doc', None)
        if not doc or not doc.is_open:
            return

        from app.ui.extract_dialog import ExtractPagesDialog
        dlg = ExtractPagesDialog(
            self.app_ref,
            doc.doc,
            selected_pages=self._selected_pages if self._selected_pages else None
        )
        self.app_ref.wait_window(dlg)

        result = dlg.result
        if result and result.get("delete_after"):
            pages_to_delete = result["pages"]
            remaining = doc.page_count - len(pages_to_delete)
            if remaining < 1:
                messagebox.showwarning("Delete", "Cannot delete all pages.")
            else:
                from app.core.page_operations import delete_pages
                delete_pages(doc.doc, pages_to_delete)
                doc.modified = True
                self._selected_pages.clear()
                self.app_ref.main_window.viewport.load_document()
                self.app_ref.main_window.sidebar.refresh()
                self._render_grid()

    def _do_delete(self):
        if not self._selected_pages:
            messagebox.showinfo("Delete", "No pages selected.")
            return
        doc = getattr(self.app_ref, 'pdf_doc', None)
        if not doc or not doc.is_open:
            return

        remaining = doc.page_count - len(self._selected_pages)
        if remaining < 1:
            messagebox.showwarning("Delete", "Cannot delete all pages.")
            return

        pages_sorted = sorted(self._selected_pages)
        page_str = ", ".join(str(p + 1) for p in pages_sorted)
        confirm = messagebox.askyesno(
            "Delete Pages",
            f"Delete page(s) {page_str}?\nThis cannot be undone."
        )
        if not confirm:
            return

        from app.core.page_operations import delete_pages
        delete_pages(doc.doc, pages_sorted)
        doc.modified = True
        self._selected_pages.clear()
        self.app_ref.main_window.viewport.load_document()
        self.app_ref.main_window.sidebar.refresh()
        self._render_grid()

    def _go_to_page(self, page_num: int):
        self.hide()
        vp = self.app_ref.main_window.viewport
        vp.go_to_page(page_num)
        self.app_ref.update_status()
        self.app_ref.main_window.sidebar.highlight_page(page_num)
