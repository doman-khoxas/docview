"""DocView search bar — Cyber-Brutalist terminal-style search row.

Strict theme compliance: BG_ABYSS, BORDER_RED, TEXT_RED, HOVER_RED.
All corner_radius=0. All text in Courier. Thick borders. Harsh aesthetic.
"""
import customtkinter as ctk
from app.config import (
    BG_ABYSS, BG_PANEL, BORDER_RED, TEXT_RED,
    HOVER_RED, ACTIVE_RED, COLOR_DANGER, TEXT_MUTED
)
from app.logger import get_logger

logger = get_logger(__name__)

_FONT = ctk.CTkFont(family="Courier", size=12)
_FONT_SM = ctk.CTkFont(family="Courier", size=11)
_FONT_BTN = ctk.CTkFont(family="Courier", size=11, weight="bold")


class SearchPanel(ctk.CTkFrame):
    """Harsh terminal-style search bar. Zero radius. Thick borders. Courier."""

    def __init__(self, parent, app_ref):
        super().__init__(
            parent, height=38, fg_color=BG_PANEL,
            border_color=BORDER_RED, border_width=2,
            corner_radius=0
        )
        self.app_ref = app_ref
        self.pack_propagate(False)
        self._results: list[tuple[int, list]] = []
        self._current_idx = -1
        self._flat_results: list[tuple[int, int]] = []

        # --- FIND> prompt label ---
        ctk.CTkLabel(
            self, text="FIND>",
            font=_FONT_BTN, text_color=COLOR_DANGER
        ).pack(side="left", padx=(6, 2))

        # --- Search entry ---
        self._entry_var = ctk.StringVar()
        self._entry = ctk.CTkEntry(
            self, textvariable=self._entry_var,
            width=240, height=28,
            placeholder_text="search term...",
            fg_color=BG_ABYSS,
            border_color=BORDER_RED, border_width=2,
            text_color=TEXT_RED,
            placeholder_text_color=TEXT_MUTED,
            font=_FONT,
            corner_radius=0
        )
        self._entry.pack(side="left", padx=(2, 4), pady=4)
        self._entry.bind("<Return>", lambda e: self._do_search())

        # --- EXEC button ---
        ctk.CTkButton(
            self, text="EXEC", width=50, height=26,
            fg_color=BG_ABYSS, hover_color=HOVER_RED,
            border_color=BORDER_RED, border_width=2,
            text_color=TEXT_RED, font=_FONT_BTN,
            corner_radius=0, command=self._do_search
        ).pack(side="left", padx=2)

        # --- Case toggle ---
        self._case_var = ctk.BooleanVar(value=False)
        self._case_cb = ctk.CTkCheckBox(
            self, text="Aa", variable=self._case_var,
            width=36, height=26,
            font=_FONT_SM, text_color=TEXT_RED,
            fg_color=COLOR_DANGER, hover_color=HOVER_RED,
            border_color=BORDER_RED, border_width=2,
            corner_radius=0, checkbox_width=16, checkbox_height=16,
            command=self._do_search
        )
        self._case_cb.pack(side="left", padx=4)

        # --- Nav buttons ---
        ctk.CTkButton(
            self, text="<", width=26, height=26,
            fg_color=BG_ABYSS, hover_color=HOVER_RED,
            border_color=BORDER_RED, border_width=2,
            text_color=TEXT_RED, font=_FONT_BTN,
            corner_radius=0, command=self._prev_result
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            self, text=">", width=26, height=26,
            fg_color=BG_ABYSS, hover_color=HOVER_RED,
            border_color=BORDER_RED, border_width=2,
            text_color=TEXT_RED, font=_FONT_BTN,
            corner_radius=0, command=self._next_result
        ).pack(side="left", padx=1)

        # --- Result count ---
        self._count_label = ctk.CTkLabel(
            self, text="",
            font=_FONT_SM, text_color=TEXT_MUTED
        )
        self._count_label.pack(side="left", padx=8)

        # --- Close [X] ---
        ctk.CTkButton(
            self, text="X", width=26, height=26,
            fg_color=BG_ABYSS, hover_color=COLOR_DANGER,
            border_color=BORDER_RED, border_width=2,
            text_color=COLOR_DANGER, font=_FONT_BTN,
            corner_radius=0, command=self.close
        ).pack(side="right", padx=4)

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

        match_case = self._case_var.get()

        for pn in range(doc.page_count):
            page = doc.get_page(pn)
            rects = page.search_for(query)
            if match_case and rects:
                filtered = []
                for r in rects:
                    text = page.get_textbox(r)
                    if query in text:
                        filtered.append(r)
                rects = filtered
            if rects:
                self._results.append((pn, rects))
                for ri in range(len(rects)):
                    self._flat_results.append((pn, ri))

        vp = self.app_ref.main_window.viewport
        vp.highlight_search_results(self._results)

        total = len(self._flat_results)
        logger.info("Search '%s': %d hit(s) / %d page(s)",
                     query, total, len(self._results))
        if total > 0:
            self._current_idx = 0
            self._navigate_to_current()
        else:
            self._current_idx = -1
            self._count_label.configure(text="0 HITS")

    def _navigate_to_current(self):
        if not self._flat_results or self._current_idx < 0:
            return
        total = len(self._flat_results)
        page_num, _ = self._flat_results[self._current_idx]
        self.app_ref.main_window.viewport.go_to_page(page_num)
        self._count_label.configure(
            text=f"{self._current_idx + 1}/{total}")

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
