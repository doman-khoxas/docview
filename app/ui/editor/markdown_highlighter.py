"""QSyntaxHighlighter for Markdown with Obsidian wikilink support."""
import re
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PyQt5.QtCore import QRegularExpression
from app.ui.theme import ACCENT, SUCCESS, WARNING, ERROR, INFO, TEXT_SECONDARY


class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown documents."""

    def __init__(self, document=None):
        super().__init__(document)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._setup_rules()

    def _make_fmt(self, color: str, bold=False, italic=False, font_family=None) -> QTextCharFormat:
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if italic:
            fmt.setFontItalic(True)
        if font_family:
            fmt.setFontFamily(font_family)
        return fmt

    def _setup_rules(self):
        # Headers
        h1_fmt = self._make_fmt("#569cd6", bold=True)
        h1_fmt.setFontPointSize(20)
        self._rules.append((QRegularExpression(r'^# .+$'), h1_fmt))

        h2_fmt = self._make_fmt("#569cd6", bold=True)
        h2_fmt.setFontPointSize(17)
        self._rules.append((QRegularExpression(r'^## .+$'), h2_fmt))

        h3_fmt = self._make_fmt("#569cd6", bold=True)
        h3_fmt.setFontPointSize(14)
        self._rules.append((QRegularExpression(r'^### .+$'), h3_fmt))

        h456_fmt = self._make_fmt("#569cd6", bold=True)
        self._rules.append((QRegularExpression(r'^#{4,6} .+$'), h456_fmt))

        # Bold **text** or __text__
        self._rules.append((QRegularExpression(r'\*\*[^*]+\*\*'), self._make_fmt("#d4d4d4", bold=True)))
        self._rules.append((QRegularExpression(r'__[^_]+__'), self._make_fmt("#d4d4d4", bold=True)))

        # Italic *text* or _text_
        self._rules.append((QRegularExpression(r'(?<!\*)\*(?!\*)[^*]+\*(?!\*)'), self._make_fmt("#d4d4d4", italic=True)))
        self._rules.append((QRegularExpression(r'(?<!_)_(?!_)[^_]+_(?!_)'), self._make_fmt("#d4d4d4", italic=True)))

        # Inline code `text`
        self._rules.append((QRegularExpression(r'`[^`]+`'), self._make_fmt("#ce9178", font_family="Consolas")))

        # Wikilinks [[link]] or [[link|display]]
        self._rules.append((QRegularExpression(r'\[\[[^\]]+\]\]'), self._make_fmt(ACCENT, bold=True)))

        # Standard links [text](url)
        self._rules.append((QRegularExpression(r'\[[^\]]*\]\([^\)]*\)'), self._make_fmt(ACCENT)))

        # Images ![alt](url)
        self._rules.append((QRegularExpression(r'!\[[^\]]*\]\([^\)]*\)'), self._make_fmt("#b5cea8")))

        # Blockquotes > text
        self._rules.append((QRegularExpression(r'^>\s.*$'), self._make_fmt("#608b4e", italic=True)))

        # Horizontal rules ---
        self._rules.append((QRegularExpression(r'^---+\s*$'), self._make_fmt(TEXT_SECONDARY)))

        # Unordered list - item
        self._rules.append((QRegularExpression(r'^\s*[-*+]\s'), self._make_fmt("#d7ba7d")))

        # Ordered list 1. item
        self._rules.append((QRegularExpression(r'^\s*\d+\.\s'), self._make_fmt("#d7ba7d")))

        # Tags #tag
        self._rules.append((QRegularExpression(r'(?:^|\s)#[a-zA-Z0-9_/]+'), self._make_fmt("#4ec9b0")))

        # YAML frontmatter markers
        self._rules.append((QRegularExpression(r'^---\s*$'), self._make_fmt("#808080")))

        # Strikethrough ~~text~~
        strikethrough_fmt = self._make_fmt(TEXT_SECONDARY)
        strikethrough_fmt.setFontStrikeOut(True)
        self._rules.append((QRegularExpression(r'~~[^~]+~~'), strikethrough_fmt))

    def highlightBlock(self, text: str):
        # Check for code block state
        self._highlight_code_blocks(text)

        # Apply inline rules only if not in code block
        if self.currentBlockState() != 1:
            for pattern, fmt in self._rules:
                match_iter = pattern.globalMatch(text)
                while match_iter.hasNext():
                    match = match_iter.next()
                    self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

    def _highlight_code_blocks(self, text: str):
        """Handle fenced code blocks (```...```)."""
        code_fmt = self._make_fmt("#ce9178", font_family="Consolas")
        fence_fmt = self._make_fmt("#808080")

        # Check if previous block was inside a code fence
        prev_state = self.previousBlockState()

        if prev_state == 1:
            # We're inside a code block
            if text.strip().startswith('```'):
                # End of code block
                self.setFormat(0, len(text), fence_fmt)
                self.setCurrentBlockState(0)
            else:
                self.setFormat(0, len(text), code_fmt)
                self.setCurrentBlockState(1)
        else:
            if text.strip().startswith('```'):
                # Start of code block
                self.setFormat(0, len(text), fence_fmt)
                self.setCurrentBlockState(1)
            else:
                self.setCurrentBlockState(0)
