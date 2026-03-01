"""Dialog for inserting a blank page or pages from another PDF."""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.core.page_operations import insert_blank_page, insert_pages_from_file


class InsertPageDialog(ctk.CTkToplevel):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.app_ref = app_ref
        self.title("Insert Page")
        self.geometry("380x250")

        doc = app_ref.pdf_doc
        if not doc.is_open:
            self.destroy()
            return

        vp = app_ref.main_window.viewport
        current = vp.current_page

        ctk.CTkLabel(self, text="Insert page after:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 5))

        pos_frame = ctk.CTkFrame(self, fg_color="transparent")
        pos_frame.pack(pady=5)
        ctk.CTkLabel(pos_frame, text="After page:").pack(side="left", padx=5)
        self._pos_entry = ctk.CTkEntry(pos_frame, width=60)
        self._pos_entry.pack(side="left")
        self._pos_entry.insert(0, str(current + 1))

        self._mode = ctk.StringVar(value="blank")
        ctk.CTkRadioButton(self, text="Insert blank page", variable=self._mode, value="blank").pack(pady=5)
        ctk.CTkRadioButton(self, text="Insert from file", variable=self._mode, value="file").pack(pady=5)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=15)
        ctk.CTkButton(action_frame, text="Insert", width=100, command=self._insert).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="Cancel", width=100, command=self.destroy).pack(side="left", padx=5)

    def _insert(self):
        try:
            pos = int(self._pos_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid page number.", parent=self)
            return

        doc = self.app_ref.pdf_doc

        if self._mode.get() == "blank":
            insert_blank_page(doc.doc, pos)
            doc.modified = True
        else:
            path = filedialog.askopenfilename(
                filetypes=[("PDF files", "*.pdf")], parent=self
            )
            if not path:
                return
            try:
                insert_pages_from_file(doc.doc, pos, path)
                doc.modified = True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to insert pages:\n{e}", parent=self)
                return

        self.app_ref.main_window.viewport.load_document()
        self.app_ref.main_window.sidebar.refresh()
        self.app_ref.update_status()
        self.destroy()
