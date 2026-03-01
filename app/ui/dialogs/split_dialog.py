"""Dialog for splitting a PDF into parts by page ranges."""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from app.core.page_operations import split_pdf


class SplitDialog(ctk.CTkToplevel):
    def __init__(self, app_ref):
        super().__init__(app_ref)
        self.app_ref = app_ref
        self.title("Split PDF")
        self.geometry("400x300")

        doc = app_ref.pdf_doc
        total = doc.page_count

        ctk.CTkLabel(self, text=f"Total pages: {total}",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 5))

        ctk.CTkLabel(self, text="Page ranges (e.g. 1-3, 4-6, 7-10):").pack(pady=5)

        self._ranges_entry = ctk.CTkEntry(self, width=300)
        self._ranges_entry.pack(padx=20, pady=5)
        self._ranges_entry.insert(0, f"1-{total}")

        sep = ctk.CTkFrame(self, height=2, fg_color="gray50")
        sep.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self, text="— OR split every N pages —").pack(pady=5)

        every_frame = ctk.CTkFrame(self, fg_color="transparent")
        every_frame.pack(pady=5)
        ctk.CTkLabel(every_frame, text="Every").pack(side="left", padx=5)
        self._every_entry = ctk.CTkEntry(every_frame, width=50)
        self._every_entry.pack(side="left")
        ctk.CTkLabel(every_frame, text="pages").pack(side="left", padx=5)

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=15)
        ctk.CTkButton(action_frame, text="Split", width=100, command=self._split).pack(side="left", padx=5)
        ctk.CTkButton(action_frame, text="Cancel", width=100, command=self.destroy).pack(side="left", padx=5)

    def _parse_ranges(self) -> list[tuple[int, int]] | None:
        every_text = self._every_entry.get().strip()
        doc = self.app_ref.pdf_doc
        total = doc.page_count

        if every_text:
            try:
                n = int(every_text)
                if n < 1:
                    raise ValueError
                ranges = []
                for start in range(0, total, n):
                    end = min(start + n - 1, total - 1)
                    ranges.append((start, end))
                return ranges
            except ValueError:
                messagebox.showerror("Error", "Invalid number for 'every N pages'.", parent=self)
                return None

        text = self._ranges_entry.get().strip()
        if not text:
            messagebox.showerror("Error", "Enter page ranges.", parent=self)
            return None

        ranges = []
        for part in text.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                try:
                    start = int(a.strip()) - 1
                    end = int(b.strip()) - 1
                    if start < 0 or end >= total or start > end:
                        raise ValueError
                    ranges.append((start, end))
                except ValueError:
                    messagebox.showerror("Error", f"Invalid range: {part}", parent=self)
                    return None
            else:
                try:
                    p = int(part) - 1
                    if p < 0 or p >= total:
                        raise ValueError
                    ranges.append((p, p))
                except ValueError:
                    messagebox.showerror("Error", f"Invalid page: {part}", parent=self)
                    return None
        return ranges

    def _split(self):
        ranges = self._parse_ranges()
        if not ranges:
            return

        output_dir = filedialog.askdirectory(title="Select output directory", parent=self)
        if not output_dir:
            return

        doc = self.app_ref.pdf_doc
        base_name = Path(doc.file_path).stem if doc.file_path else "split"

        try:
            files = split_pdf(doc.doc, ranges, output_dir, base_name)
            messagebox.showinfo("Split", f"Created {len(files)} file(s):\n" + "\n".join(files), parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Split failed:\n{e}", parent=self)
