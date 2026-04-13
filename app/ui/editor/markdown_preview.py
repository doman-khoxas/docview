"""Live HTML preview for markdown documents."""
import re
import markdown
from PyQt5.QtWidgets import QTextBrowser
from PyQt5.QtCore import pyqtSignal
from app.config import MD_PREVIEW_CSS_BG, MD_PREVIEW_CSS_FG
from app.ui.theme import ACCENT, BG_SURFACE


# CSS for the preview
PREVIEW_CSS = f"""
body {{
    background-color: {MD_PREVIEW_CSS_BG};
    color: {MD_PREVIEW_CSS_FG};
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    padding: 16px 24px;
    max-width: 800px;
}}
h1 {{ color: #569cd6; border-bottom: 1px solid #333; padding-bottom: 8px; }}
h2 {{ color: #569cd6; }}
h3, h4, h5, h6 {{ color: #569cd6; }}
a {{ color: {ACCENT}; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
code {{
    background-color: {BG_SURFACE};
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Consolas', monospace;
    font-size: 13px;
}}
pre {{
    background-color: {BG_SURFACE};
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
}}
pre code {{
    padding: 0;
    background: none;
}}
blockquote {{
    border-left: 3px solid {ACCENT};
    margin-left: 0;
    padding-left: 16px;
    color: #858585;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
}}
th, td {{
    border: 1px solid #333;
    padding: 6px 12px;
    text-align: left;
}}
th {{
    background-color: {BG_SURFACE};
}}
hr {{
    border: none;
    border-top: 1px solid #333;
    margin: 16px 0;
}}
img {{
    max-width: 100%;
}}
.wikilink {{
    color: {ACCENT};
    font-weight: bold;
    cursor: pointer;
}}
"""

# Wikilink pattern for post-processing HTML
WIKILINK_HTML_RE = re.compile(r'\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]')


class MarkdownPreview(QTextBrowser):
    """Renders markdown as HTML with wikilink support."""

    wikilink_clicked = pyqtSignal(str)  # target name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenLinks(False)
        self.anchorClicked.connect(self._on_link_clicked)
        self.setStyleSheet(f"""
            QTextBrowser {{
                border: none;
                background-color: {MD_PREVIEW_CSS_BG};
            }}
        """)

        # Only use extensions that PyInstaller reliably bundles
        exts = []
        for ext in ['tables', 'fenced_code', 'toc', 'nl2br', 'sane_lists', 'meta', 'codehilite']:
            try:
                markdown.Markdown(extensions=[ext])
                exts.append(ext)
            except Exception:
                pass
        self._md = markdown.Markdown(extensions=exts)

    def update_preview(self, text: str):
        """Convert markdown text to HTML and display."""
        self._md.reset()
        html = self._md.convert(text)

        # Convert wikilinks to clickable HTML
        html = WIKILINK_HTML_RE.sub(self._wikilink_to_html, html)

        full_html = f"""
        <html>
        <head><style>{PREVIEW_CSS}</style></head>
        <body>{html}</body>
        </html>
        """
        # Preserve scroll position
        scroll_val = self.verticalScrollBar().value()
        self.setHtml(full_html)
        self.verticalScrollBar().setValue(scroll_val)

    @staticmethod
    def _wikilink_to_html(match) -> str:
        target = match.group(1).strip()
        display = match.group(2).strip() if match.group(2) else target
        return f'<a href="wikilink://{target}" class="wikilink">{display}</a>'

    def _on_link_clicked(self, url):
        scheme = url.scheme()
        if scheme == "wikilink":
            target = url.host() or url.path().lstrip('/')
            self.wikilink_clicked.emit(target)
        else:
            import webbrowser
            webbrowser.open(url.toString())
