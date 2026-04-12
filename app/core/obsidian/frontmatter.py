"""YAML frontmatter parsing and serialization."""
import re
import yaml

FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from markdown text.

    Returns (frontmatter_dict, body_text).
    If no frontmatter found, returns ({}, original_text).
    """
    match = FRONTMATTER_RE.match(text)
    if match:
        try:
            data = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            data = {}
        body = text[match.end():]
        return data, body
    return {}, text


def serialize_frontmatter(data: dict, body: str) -> str:
    """Combine frontmatter dict and body into complete markdown text."""
    if not data:
        return body
    fm = yaml.dump(data, default_flow_style=False, allow_unicode=True).strip()
    return f"---\n{fm}\n---\n\n{body}"


def update_frontmatter(text: str, updates: dict) -> str:
    """Update specific frontmatter fields without touching the rest."""
    data, body = parse_frontmatter(text)
    data.update(updates)
    return serialize_frontmatter(data, body)
