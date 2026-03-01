"""Export/Save-As dialog with flatten option."""
import customtkinter as ctk
from tkinter import filedialog, messagebox


class ExportDialog(ctk.CTkToplevel):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.app_ref = app_ref
        self.title("Export PDF")
        self.geometry("380x180")

        doc = app_ref.pdf_doc
        if not doc.is_open:
            self.destroy()
            return

        ctk.CTkLabel(self, text="Export Options",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 5))

        self._flatten_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self, text="Flatten annotations (burn into page)",
                        variable=self._flatten_var).pack(pady=10)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=15)
        ctk.CTkButton(action_frame, text="Export", width=100, command=self._export).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="Cancel", width=100, command=self.destroy).pack(side="left", padx=5)

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            parent=self
        )
        if not path:
            return

        try:
            self.app_ref.pdf_doc.save_as(path, flatten=self._flatten_var.get())
            messagebox.showinfo("Export", f"Exported to:\n{path}", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Export failed:\n{e}", parent=self)
