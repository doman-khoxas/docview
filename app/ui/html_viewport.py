"""HTML/Markdown viewport — renders HTML and Markdown files in the app."""
import tkinter as tk
from pathlib import Path
from app.config import BG_DEEP, BG_PANEL, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, BORDER_SUBTLE
from app.logger import get_logger

logger = get_logger(__name__)

# Dark theme CSS injected into all rendered HTML
_DARK_CSS = """
<style>
body {
    background-color: #1A1B1E;
    color: #E1E2E4;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 14px;
    line-height: 1.6;
    padding: 24px 32px;
    max-width: 900px;
    margin: 0 auto;
}
h1 { color: #4A9EFF; font-size: 28px; border-bottom: 2px solid #44464B; padding-bottom: 8px; margin-top: 24px; }
h2 { color: #5AADFF; font-size: 22px; border-bottom: 1px solid #35373B; padding-bottom: 6px; margin-top: 20px; }
h3 { color: #6BBFFF; font-size: 18px; margin-top: 16px; }
h4, h5, h6 { color: #A0A1A4; margin-top: 12px; }
p { margin: 8px 0; }
a { color: #4A9EFF; text-decoration: none; }
a:hover { text-decoration: underline; }
code {
    background-color: #2B2D31;
    color: #E1E2E4;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
}
pre {
    background-color: #2B2D31;
    border: 1px solid #44464B;
    border-radius: 6px;
    padding: 12px 16px;
    overflow-x: auto;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
    line-height: 1.5;
}
pre code { background: none; padding: 0; }
blockquote {
    border-left: 4px solid #4A9EFF;
    margin: 12px 0;
    padding: 8px 16px;
    background-color: #222327;
    color: #A0A1A4;
}
table { border-collapse: collapse; width: 100%; margin: 12px 0; }
th {
    background-color: #2B2D31;
    color: #4A9EFF;
    padding: 8px 12px;
    text-align: left;
    border: 1px solid #44464B;
    font-weight: bold;
}
td {
    padding: 8px 12px;
    border: 1px solid #44464B;
}
tr:nth-child(even) { background-color: #222327; }
ul, ol { padding-left: 24px; margin: 8px 0; }
li { margin: 4px 0; }
hr { border: none; border-top: 1px solid #44464B; margin: 20px 0; }
img { max-width: 100%; border-radius: 4px; }
strong { color: #E1E2E4; }
em { color: #A0A1A4; }
</style>
"""


def _convert_markdown_to_html(md_text: str) -> str:
    """Convert markdown text to HTML string."""
    try:
        import markdown
        html = markdown.markdown(
            md_text,
            extensions=['tables', 'fenced_code', 'codehilite', 'toc', 'nl2br']
        )
        return html
    except ImportError:
        logger.warning("markdown module not available, rendering as plain text")
        escaped = md_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<pre>{escaped}</pre>"


def _wrap_html(body_html: str, title: str = "") -> str:
    """Wrap HTML body content with dark theme styling."""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
{_DARK_CSS}
</head>
<body>
{body_html}
</body>
</html>"""


class HTMLViewport(tk.Frame):
    """Viewport for rendering HTML and Markdown files."""

    def __init__(self, parent, app_ref):
        super().__init__(parent, bg=BG_DEEP)
        self.app_ref = app_ref
        self._file_path = None
        self._file_type = None  # "html" or "markdown"

        # Use tkhtmlview for rendering
        from tkhtmlview import HTMLScrolledText

        self._html_widget = HTMLScrolledText(
            self,
            html="",
            background=BG_DEEP,
            padx=16,
            pady=16,
        )
        self._html_widget.pack(fill="both", expand=True)

    def load_file(self, file_path: str):
        """Load and render an HTML or Markdown file."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1")

        if suffix in (".md", ".markdown", ".mdown", ".mkd"):
            self._file_type = "markdown"
            body_html = _convert_markdown_to_html(content)
            full_html = _wrap_html(body_html, title=path.name)
            logger.info("Loaded Markdown file: %s (%d chars)", path.name, len(content))
        elif suffix in (".html", ".htm"):
            self._file_type = "html"
            # If the HTML doesn't have our dark theme, inject it
            if "<style>" not in content and "<link" not in content:
                full_html = _wrap_html(content, title=path.name)
            else:
                full_html = content
            logger.info("Loaded HTML file: %s (%d chars)", path.name, len(content))
        else:
            # Plain text fallback
            self._file_type = "text"
            escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            full_html = _wrap_html(f"<pre>{escaped}</pre>", title=path.name)
            logger.info("Loaded text file as HTML: %s", path.name)

        self._file_path = str(path)
        self._html_widget.set_html(full_html)

    @property
    def file_path(self) -> str | None:
        return self._file_path

    @property
    def file_type(self) -> str | None:
        return self._file_type
