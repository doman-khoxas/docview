"""OneNote import — handles .one binary files, HTML exports, and folder structures."""
import re
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.core.obsidian.frontmatter import serialize_frontmatter

ONESTORE_MAGIC = bytes.fromhex('e4525c7b8cd8a74daeb15378d02996d3')
SKIP_SUFFIXES = {'.onetoc2'}


# ═══════════════════════════════════════════════════
# .one binary text extraction
# ═══════════════════════════════════════════════════

def _extract_text_from_one(path: Path) -> str:
    """Extract readable text from a .one binary file (ONESTORE format)."""
    data = path.read_bytes()
    if len(data) < 16 or data[:16] != ONESTORE_MAGIC:
        return ""

    # Extract only clean ASCII runs — the ONESTORE format stores page text
    # as UTF-16LE where real content is ASCII-range characters (hi byte = 0).
    # Binary structure bytes produce non-ASCII hi bytes — we skip those.
    runs = []
    current = []
    i = 0

    while i < len(data) - 1:
        lo, hi = data[i], data[i + 1]
        if hi == 0 and (32 <= lo < 127 or lo in (9, 10, 13)):
            current.append(chr(lo))
        else:
            if len(current) >= 4:
                runs.append(''.join(current).strip())
            current = []
        i += 2

    if len(current) >= 4:
        runs.append(''.join(current).strip())

    # Filter out OneNote internal metadata strings
    noise = {
        'PageTitle', 'PageDateTime', 'Calibri', 'Calibri Light',
        'Courier New', 'Segoe UI', 'Arial', 'Times New Roman',
        'resolutionId', 'provider=', 'localId', 'hash=',
        'xmlns', 'one:', 'CDATA', 'onenote',
        'color:', 'font-size:', 'font-family:', 'font-weight:',
        'style=', 'span ', 'lang=', 'xml:',
    }

    filtered = []
    seen = set()
    for run in runs:
        if not run or len(run) < 3:
            continue
        # Skip metadata/XML/CSS fragments
        if any(n in run for n in noise):
            continue
        if run.startswith('<') or run.startswith('{') or run.startswith('//'):
            continue
        # Skip pure hex/encoded strings
        if re.match(r'^[A-Fa-f0-9+/=]{8,}$', run):
            continue
        # Skip font names and style declarations
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', run) and len(run) < 25:
            # Could be a name like "Sampson, Liam" — keep if has comma
            if ',' not in run:
                continue
        # Deduplicate consecutive identical runs
        if run in seen and len(run) < 30:
            continue
        seen.add(run)
        filtered.append(run)

    if not filtered:
        return ""

    # Group into paragraphs — runs separated by newlines
    return '\n\n'.join(filtered)


# ═══════════════════════════════════════════════════
# HTML to Markdown
# ═══════════════════════════════════════════════════

class _HTMLToMarkdown(HTMLParser):
    def __init__(self):
        super().__init__()
        self._md = []
        self._in_pre = False
        self._in_heading = 0
        self._list_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self._in_heading = int(tag[1])
            self._md.append('\n' + '#' * self._in_heading + ' ')
        elif tag == 'p':
            self._md.append('\n\n')
        elif tag == 'br':
            self._md.append('\n')
        elif tag in ('b', 'strong'):
            self._md.append('**')
        elif tag in ('i', 'em'):
            self._md.append('*')
        elif tag in ('pre', 'code'):
            self._in_pre = True
            self._md.append('\n```\n')
        elif tag in ('ul', 'ol'):
            self._list_depth += 1
        elif tag == 'li':
            self._md.append(f"\n{'  ' * (self._list_depth - 1)}- ")
        elif tag == 'a':
            self._pending_href = dict(attrs).get('href', '')
            self._md.append('[')
        elif tag == 'img':
            d = dict(attrs)
            self._md.append(f"![{d.get('alt', 'image')}]({d.get('src', '')})")
        elif tag == 'hr':
            self._md.append('\n---\n')
        elif tag == 'blockquote':
            self._md.append('\n> ')

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self._in_heading = 0
            self._md.append('\n')
        elif tag in ('b', 'strong'):
            self._md.append('**')
        elif tag in ('i', 'em'):
            self._md.append('*')
        elif tag in ('pre', 'code'):
            self._in_pre = False
            self._md.append('\n```\n')
        elif tag in ('ul', 'ol'):
            self._list_depth = max(0, self._list_depth - 1)
        elif tag == 'a':
            self._md.append(f"]({getattr(self, '_pending_href', '')})")

    def handle_data(self, data):
        if self._in_pre:
            self._md.append(data)
        else:
            text = data.strip()
            if text:
                self._md.append(text)

    def get_markdown(self) -> str:
        return re.sub(r'\n{3,}', '\n\n', ''.join(self._md)).strip()


def html_to_markdown(html: str) -> str:
    parser = _HTMLToMarkdown()
    parser.feed(html)
    return parser.get_markdown()


# ═══════════════════════════════════════════════════
# Main import
# ═══════════════════════════════════════════════════

def import_onenote_folder(source_dir: str, vault) -> int:
    """Import a OneNote notebook folder into the vault.

    Handles .one binary files and HTML exports. Preserves folder structure.
    """
    source = Path(source_dir)
    if not source.is_dir():
        raise ValueError(f"Not a directory: {source}")

    now = datetime.now().isoformat()
    notebook = vault.create_notebook(source.name)
    count = 0

    # Top-level .one files → "General" section
    one_files = [f for f in source.iterdir()
                 if f.is_file() and f.suffix.lower() in ('.one',)]
    html_files = [f for f in source.iterdir()
                  if f.is_file() and f.suffix.lower() in ('.htm', '.html')]

    if one_files or html_files:
        section = vault.create_section(notebook, "General")
        for f in one_files:
            count += _import_one_file(f, section, vault, now)
        for f in html_files:
            count += _import_html_file(f, section, vault, now)

    # Recurse subdirectories
    for d in sorted(source.iterdir()):
        if d.is_dir() and not d.name.startswith('.') and not d.name.startswith('_'):
            count += _import_subdir(d, notebook, vault, now)

    return count


def _import_subdir(subdir: Path, notebook, vault, now: str) -> int:
    count = 0
    section = vault.create_section(notebook, subdir.name)

    for f in subdir.iterdir():
        if f.is_file():
            if f.suffix.lower() == '.one':
                count += _import_one_file(f, section, vault, now)
            elif f.suffix.lower() in ('.htm', '.html'):
                count += _import_html_file(f, section, vault, now)

    for d in sorted(subdir.iterdir()):
        if d.is_dir() and not d.name.startswith('.') and not d.name.startswith('_'):
            count += _import_subdir(d, notebook, vault, now)

    return count


def _import_one_file(path: Path, section, vault, now: str) -> int:
    if path.suffix.lower() in SKIP_SUFFIXES:
        return 0
    try:
        body = _extract_text_from_one(path)
        title = path.stem

        if not body.strip():
            body = f"*(Imported from {path.name} — binary content could not be extracted)*\n"

        page = vault.create_page(section, title)
        fm = {
            'title': title,
            'created': now,
            'modified': now,
            'tags': ['imported', 'onenote'],
            'source_file': path.name,
            'pinned': False,
        }
        page.path.write_text(serialize_frontmatter(fm, body), encoding='utf-8')
        return 1
    except Exception as e:
        print(f"  WARNING: Failed to import {path.name}: {e}")
        return 0


def _import_html_file(path: Path, section, vault, now: str) -> int:
    try:
        html = path.read_text(encoding='utf-8', errors='replace')
        body = html_to_markdown(html)
        title = path.stem

        page = vault.create_page(section, title)
        fm = {
            'title': title,
            'created': now,
            'modified': now,
            'tags': ['imported', 'onenote'],
            'pinned': False,
        }
        page.path.write_text(serialize_frontmatter(fm, body), encoding='utf-8')
        return 1
    except Exception:
        return 0
