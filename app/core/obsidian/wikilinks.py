"""Wikilink parsing and resolution for Obsidian compatibility."""
import re
from pathlib import Path

# Matches [[link]] and [[link|display text]]
WIKILINK_RE = re.compile(r'\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]')


def extract_wikilinks(text: str) -> list[dict]:
    """Extract all wikilinks from text.

    Returns list of dicts with keys: 'target', 'display', 'start', 'end'.
    """
    results = []
    for match in WIKILINK_RE.finditer(text):
        target = match.group(1).strip()
        display = match.group(2).strip() if match.group(2) else target
        results.append({
            'target': target,
            'display': display,
            'start': match.start(),
            'end': match.end(),
        })
    return results


def resolve_wikilink(target: str, vault_root: str, current_file: str | None = None) -> str | None:
    """Resolve a wikilink target to an absolute file path.

    Uses Obsidian's resolution rules:
    1. Exact filename match (case-insensitive)
    2. Shortest unique path match
    """
    vault = Path(vault_root)
    if not vault.is_dir():
        return None

    target_lower = target.lower()
    if not target_lower.endswith('.md'):
        target_lower += '.md'

    candidates = []
    for md_file in vault.rglob('*.md'):
        if md_file.name.lower() == target_lower:
            candidates.append(md_file)

    if not candidates:
        return None

    if len(candidates) == 1:
        return str(candidates[0])

    # Multiple matches: prefer shortest path
    candidates.sort(key=lambda p: len(str(p)))
    return str(candidates[0])


def find_backlinks(target_file: str, vault_root: str) -> list[str]:
    """Find all files in the vault that link to the target file.

    Returns list of absolute file paths that contain wikilinks to target.
    """
    vault = Path(vault_root)
    target = Path(target_file)
    target_name = target.stem.lower()

    backlinks = []
    for md_file in vault.rglob('*.md'):
        if md_file == target:
            continue
        try:
            text = md_file.read_text(encoding='utf-8', errors='ignore')
            links = extract_wikilinks(text)
            for link in links:
                if link['target'].lower() == target_name:
                    backlinks.append(str(md_file))
                    break
        except (OSError, UnicodeDecodeError):
            continue

    return backlinks
