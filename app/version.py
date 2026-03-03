"""
DocView Version Management

Centralized version tracking with semantic versioning (SemVer).
Used by: build system, About dialog, update checker, changelog.

Version format: MAJOR.MINOR.PATCH[-PRERELEASE]
  MAJOR — breaking changes / major UI overhaul
  MINOR — new features (backward-compatible)
  PATCH — bug fixes, polish
"""

__version__ = "2.0.0"
__version_tuple__ = (2, 0, 0)
__build_date__ = "2026-03-03"
__codename__ = "Brutalist"
__author__ = "Kazuma"
__app_name__ = "DocView"
__description__ = "Professional PDF viewer, editor, and annotator"

# Feature flags for conditional capability
FEATURES = {
    "annotations": True,
    "page_management": True,
    "compression": True,
    "digital_signatures": True,
    "metadata_strip": True,
    "redaction": True,
    "drag_reorder": True,
    "multi_document": True,
    "search": True,
    "print": True,
}


def version_string() -> str:
    """Full version string for display."""
    return f"{__app_name__} v{__version__} ({__codename__})"


def version_info() -> dict:
    """Machine-readable version info."""
    return {
        "version": __version__,
        "version_tuple": __version_tuple__,
        "build_date": __build_date__,
        "codename": __codename__,
        "author": __author__,
        "app_name": __app_name__,
        "features": FEATURES,
    }
