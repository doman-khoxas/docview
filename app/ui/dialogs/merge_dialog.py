"""Dialog for merging multiple PDF files."""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.core.page_operations import merge_pdfs


class MergeDialog(ctk.CTkToplevel):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.app_ref = app_ref
        self.title("Merge PDFs")
        self.geometry("500x400")
        self._files = []

        ctk.CTkLabel(self, text="Files to merge (in order):",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 5))

        self._listbox_frame = ctk.CTkScrollableFrame(self, height=200)
        self._listbox_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self._file_labels = []

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=5)

        ctk.CTkButton(btn_frame, text="Add Files", width=90, command=self._add_files).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Move Up", width=80, command=self._move_up).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Move Down", width=80, command=self._move_down).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Remove", width=80, command=self._remove).pack(side="left", padx=5)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=10)
        ctk.CTkButton(action_frame, text="Merge", width=100, command=self._merge).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="Cancel", width=100, command=self.destroy).pack(side="left", padx=5)

        self._selected_index = None

    def _refresh_list(self):
        for lbl in self._file_labels:
            lbl.destroy()
        self._file_labels.clear()

        for i, f in enumerate(self._files):
            lbl = ctk.CTkButton(
                self._listbox_frame, text=f, anchor="w",
                fg_color="transparent", text_color=("black", "white"),
                hover_color=("gray80", "gray30"),
                command=lambda idx=i: self._select(idx)
            )
            lbl.pack(fill="x", pady=1)
            self._file_labels.append(lbl)

    def _select(self, idx):
        self._selected_index = idx
        for i, lbl in enumerate(self._file_labels):
            if i == idx:
                lbl.configure(fg_color=("gray70", "gray40"))
            else:
                lbl.configure(fg_color="transparent")

    def _add_files(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        self._files.extend(paths)
        self._refresh_list()

    def _move_up(self):
        i = self._selected_index
        if i is not None and i > 0:
            self._files[i], self._files[i - 1] = self._files[i - 1], self._files[i]
            self._selected_index = i - 1
            self._refresh_list()

    def _move_down(self):
        i = self._selected_index
        if i is not None and i < len(self._files) - 1:
            self._files[i], self._files[i + 1] = self._files[i + 1], self._files[i]
            self._selected_index = i + 1
            self._refresh_list()

    def _remove(self):
        i = self._selected_index
        if i is not None and 0 <= i < len(self._files):
            self._files.pop(i)
            self._selected_index = None
            self._refresh_list()

    def _merge(self):
        if len(self._files) < 2:
            messagebox.showwarning("Merge", "Add at least 2 files to merge.", parent=self)
            return

        output = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")],
            parent=self
        )
        if not output:
            return

        try:
            merge_pdfs(self._files, output)
            messagebox.showinfo("Merge", f"Merged PDF saved to:\n{output}", parent=self)
            # Open the merged result
            self.app_ref.open_file(output)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Merge failed:\n{e}", parent=self)
