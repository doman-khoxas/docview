#!/usr/bin/env python3
"""
DocView -- Document Viewer & Editor
PDF Viewer | Markdown Editor | Obsidian Integration

Usage:
  GUI Mode:   python docview.py [file.pdf|file.md]
  CLI Mode:   python docview.py --cli -i file.pdf --redact "page:1,x:50,y:100,w:200,h:30" -o out.pdf
"""
import sys
from cli import build_parser, run_cli, run_combine, run_combine_manifest


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Markdown combine modes (no GUI, no PDF deps needed)
    if args.combine:
        run_combine(args)
        return
    if args.combine_manifest:
        run_combine_manifest(args)
        return

    if args.cli:
        if not args.input:
            parser.error("--cli requires --input/-i")
        run_cli(args)
    else:
        try:
            from PyQt5.QtWidgets import QApplication
        except ImportError:
            print("ERROR: PyQt5 required for GUI mode. Run: pip install PyQt5")
            print("Or use --cli for headless operation.")
            sys.exit(1)

        from app.ui.app import DocViewApp
        from app.ui.main_window import MainWindow

        app = DocViewApp(sys.argv)
        window = MainWindow(app)
        app.setup_tray(window)
        window.show()

        if args.file:
            window.open_file(args.file)

        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
