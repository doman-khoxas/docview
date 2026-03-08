"""DocView — Terminal Entry Point with crash logging and structured logging."""
import sys
import os
import traceback
from datetime import datetime


def _get_crash_log_path() -> str:
    """Return path for crashlog.txt next to the executable or script."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "crashlog.txt")


def main():
    # Initialize structured logging before anything else
    from app.logger import setup_logging, get_logger
    setup_logging()
    logger = get_logger("main")

    try:
        from app.app import DocViewApp

        file_path = sys.argv[1] if len(sys.argv) > 1 else None
        logger.info("Starting DocView application")
        if file_path:
            logger.info("CLI argument: opening file %s", file_path)

        app = DocViewApp()
        if file_path:
            app.after(100, lambda: app.open_file(file_path))

        logger.info("Entering main event loop")
        app.mainloop()
        logger.info("DocView session ended normally")

    except Exception:
        # Write crash log
        crash_path = _get_crash_log_path()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()

        crash_entry = (
            f"{'=' * 72}\n"
            f"DOCVIEW CRASH REPORT\n"
            f"Time: {timestamp}\n"
            f"Python: {sys.version}\n"
            f"Platform: {sys.platform}\n"
            f"Args: {sys.argv}\n"
            f"{'=' * 72}\n"
            f"{tb}\n\n"
        )

        # Also log to structured logger
        logger.critical("FATAL CRASH — application terminated abnormally")
        logger.critical("Traceback:\n%s", tb)

        try:
            with open(crash_path, "a", encoding="utf-8") as f:
                f.write(crash_entry)
            print(f"[CRASH] Log written to: {crash_path}", file=sys.stderr)
        except Exception:
            pass  # Last resort — can't even write log

        # Also print to stderr
        print(crash_entry, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
