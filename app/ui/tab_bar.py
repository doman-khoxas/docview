"""Horizontal document tabs with click-to-switch and close button."""
import customtkinter as ctk
from pathlib import Path
from app.config import TAB_HEIGHT, TAB_MAX_TITLE_LEN


class TabBar(ctk.CTkFrame):
    def __init__(self, parent, app_ref):
        super().__init__(parent, height=TAB_HEIGHT, fg_color=("gray85", "gray20"))
        self.app_ref = app_ref
        self.pack_propagate(False)
        self._tab_buttons: list[ctk.CTkFrame] = []

    def refresh(self):
        for w in self._tab_buttons:
            w.destroy()
        self._tab_buttons.clear()

        doc_mgr = self.app_ref.doc_manager
        for i, tab in enumerate(doc_mgr.get_all_tabs()):
            self._create_tab_widget(i, tab)

    def _create_tab_widget(self, index: int, tab):
        is_active = (index == self.app_ref.doc_manager.active_index)

        frame = ctk.CTkFrame(
            self, height=TAB_HEIGHT - 4,
            fg_color=("white", "gray30") if is_active else ("gray90", "gray22"),
            corner_radius=4)
        frame.pack(side="left", padx=(2, 0), pady=2)
        frame.pack_propagate(False)

        name = Path(tab.file_path).name if tab.file_path else "Untitled"
        if len(name) > TAB_MAX_TITLE_LEN:
            name = name[:TAB_MAX_TITLE_LEN - 2] + ".."
        if tab.pdf_doc.modified:
            name = "* " + name

        label = ctk.CTkLabel(frame, text=name, font=ctk.CTkFont(size=11),
                             cursor="hand2", padx=8)
        label.pack(side="left", fill="y")
        label.bind("<Button-1>", lambda e, idx=index: self._on_click(idx))

        close_btn = ctk.CTkButton(
            frame, text="x", width=18, height=18, font=ctk.CTkFont(size=10),
            fg_color="transparent", hover_color=("gray70", "gray45"),
            command=lambda idx=index: self._on_close(idx))
        close_btn.pack(side="right", padx=(0, 2))

        # set fixed width
        frame.configure(width=label.cget("font").cget("size") * len(name) // 2 + 50)
        frame.configure(width=min(200, max(80, len(name) * 8 + 40)))

        self._tab_buttons.append(frame)

    def _on_click(self, index: int):
        self.app_ref.switch_tab(index)

    def _on_close(self, index: int):
        self.app_ref.close_tab(index)
