"""DocView search bar — Ctrl+F with prev/next result navigation."""
import customtkinter as ctk
from app.config import (
    BG_SURFACE, BG_ABYSS, BORDER_SUBTLE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT, ACCENT_MUTED, BG_HOVER, BG_ACTIVE, CORNER_RADIUS
)


class SearchPanel(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(parent, height=36, fg_color=BG_SURFACE,
                         border_color=BORDER_SUBTLE, border_width=1,
                         corner_radius=CORNER_RADIUS)
        self.app_ref = app_ref
        self.pack_propagate(False)
        self._results: list[tuple[int, list]] = []  # [(page_num, [Rect,...]), ...]
        self._current_idx = -1
        self._flat_results: list[tuple[int, int]] = []  # [(page_num, rect_idx), ...]

        self._entry_var = ctk.StringVar()
        self._entry = ctk.CTkEntry(self, textvariable=self._entry_var,
                                   width=250, height=28, placeholder_text="Search...",
                                   fg_color=BG_ABYSS, border_color=BORDER_SUBTLE,
                                   text_color=TEXT_PRIMARY,
                                   font=ctk.CTkFont(family="Segoe UI", size=12))
        self._entry.pack(side="left", padx=(8, 4), pady=4)
        self._entry.bind("<Return>", lambda e: self._do_search())

        search_btn = ctk.CTkButton(self, text="Find", width=50, height=26,
                                   fg_color=ACCENT_MUTED, hover_color=ACCENT,
                                   text_color=TEXT_PRIMARY,
                                   font=ctk.CTkFont(family="Segoe UI", size=11),
                                   corner_radius=4,
                                   command=self._do_search)
        search_btn.pack(side="left", padx=2)

        prev_btn = ctk.CTkButton(self, text="<", width=28, height=26,
                                 fg_color="transparent", hover_color=BG_ACTIVE,
                                 text_color=TEXT_SECONDARY,
                                 font=ctk.CTkFont(family="Segoe UI", size=11),
                                 corner_radius=4,
                                 command=self._prev_result)
        prev_btn.pack(side="left", padx=1)

        next_btn = ctk.CTkButton(self, text=">", width=28, height=26,
                                 fg_color="transparent", hover_color=BG_ACTIVE,
                                 text_color=TEXT_SECONDARY,
                                 font=ctk.CTkFont(family="Segoe UI", size=11),
                                 corner_radius=4,
                                 command=self._next_result)
        next_btn.pack(side="left", padx=1)

        self._count_label = ctk.CTkLabel(self, text="",
                                         font=ctk.CTkFont(family="Segoe UI", size=11),
                                         text_color=TEXT_MUTED)
        self._count_label.pack(side="left", padx=8)

        close_btn = ctk.CTkButton(self, text="x", width=26, height=26,
                                  fg_color="transparent",
                                  hover_color=BG_ACTIVE,
                                  text_color=TEXT_SECONDARY,
                                  font=ctk.CTkFont(family="Segoe UI", size=11),
                                  corner_radius=4,
                                  command=self.close)
        close_btn.pack(side="right", padx=4)

    def open(self):
        self.pack(fill="x", side="top")
        self._entry.focus_set()
        self._entry.select_range(0, "end")

    def close(self):
        self.pack_forget()
        vp = self.app_ref.main_window.viewport
        vp.clear_search_highlights()
        self._results.clear()
        self._flat_results.clear()
        self._current_idx = -1
        self._count_label.configure(text="")

    @property
    def is_open(self) -> bool:
        return self.winfo_manager() != ""

    def _do_search(self):
        query = self._entry_var.get().strip()
        if not query:
            return

        doc = self.app_ref.pdf_doc
        if not doc or not doc.is_open:
            return

        self._results.clear()
        self._flat_results.clear()

        for pn in range(doc.page_count):
            page = doc.get_page(pn)
            rects = page.search_for(query)
            if rects:
                self._results.append((pn, rects))
                for ri in range(len(rects)):
                    self._flat_results.append((pn, ri))

        vp = self.app_ref.main_window.viewport
        vp.highlight_search_results(self._results)

        total = len(self._flat_results)
        if total > 0:
            self._current_idx = 0
            self._navigate_to_current()
        else:
            self._current_idx = -1
            self._count_label.configure(text="No results")

    def _navigate_to_current(self):
        if not self._flat_results or self._current_idx < 0:
            return
        total = len(self._flat_results)
        page_num, _ = self._flat_results[self._current_idx]
        self.app_ref.main_window.viewport.go_to_page(page_num)
        self._count_label.configure(text=f"{self._current_idx + 1} / {total}")

    def _next_result(self):
        if not self._flat_results:
            return
        self._current_idx = (self._current_idx + 1) % len(self._flat_results)
        self._navigate_to_current()

    def _prev_result(self):
        if not self._flat_results:
            return
        self._current_idx = (self._current_idx - 1) % len(self._flat_results)
        self._navigate_to_current()
