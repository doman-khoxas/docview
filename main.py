"""PDF Editor — Entry point."""
import sys
from app.app import PDFEditorApp


def main():
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = PDFEditorApp()
    if file_path:
        app.after(100, lambda: app.open_file(file_path))
    app.mainloop()


if __name__ == "__main__":
    main()
