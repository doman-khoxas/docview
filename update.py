#!/usr/bin/env python3
"""
DocView Update Utility

Manages version bumps, changelog generation, and release preparation.

Usage:
    python update.py status              # Show current version + feature status
    python update.py bump patch          # 2.0.0 → 2.0.1
    python update.py bump minor          # 2.0.0 → 2.1.0
    python update.py bump major          # 2.0.0 → 3.0.0
    python update.py changelog "message" # Add changelog entry
    python update.py release             # Prepare release (bump + changelog + tag)
    python update.py history             # Show changelog
"""

import sys
import os
import re
import argparse
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
VERSION_FILE = BASE_DIR / "app" / "version.py"
CHANGELOG_FILE = BASE_DIR / "CHANGELOG.md"


def read_version() -> str:
    """Read current version from version.py."""
    content = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return "0.0.0"


def read_version_tuple(version: str) -> tuple[int, int, int]:
    """Parse version string into (major, minor, patch)."""
    parts = version.split("-")[0].split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def write_version(new_version: str, new_tuple: tuple[int, int, int]):
    """Update version.py with new version."""
    content = VERSION_FILE.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    content = re.sub(
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    content = re.sub(
        r'__version_tuple__\s*=\s*\([^)]+\)',
        f'__version_tuple__ = {new_tuple}',
        content
    )
    content = re.sub(
        r'__build_date__\s*=\s*"[^"]+"',
        f'__build_date__ = "{today}"',
        content
    )

    VERSION_FILE.write_text(content, encoding="utf-8")


def bump_version(bump_type: str) -> str:
    """Bump version and return new version string."""
    current = read_version()
    major, minor, patch = read_version_tuple(current)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        major = major
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print(f"Unknown bump type: {bump_type}")
        sys.exit(1)

    new_version = f"{major}.{minor}.{patch}"
    new_tuple = (major, minor, patch)
    write_version(new_version, new_tuple)
    return new_version


def add_changelog_entry(message: str, version: str | None = None):
    """Add an entry to CHANGELOG.md."""
    if not version:
        version = read_version()
    today = datetime.now().strftime("%Y-%m-%d")

    entry = f"\n## [{version}] - {today}\n\n- {message}\n"

    if CHANGELOG_FILE.exists():
        content = CHANGELOG_FILE.read_text(encoding="utf-8")
        # Insert after the header
        header_end = content.find("\n## ")
        if header_end == -1:
            content += entry
        else:
            content = content[:header_end] + entry + content[header_end:]
    else:
        content = (
            "# DocView Changelog\n\n"
            "All notable changes to DocView are documented here.\n"
            "Format follows [Keep a Changelog](https://keepachangelog.com/).\n"
            f"{entry}"
        )

    CHANGELOG_FILE.write_text(content, encoding="utf-8")
    print(f"  Changelog entry added for v{version}")


def show_status():
    """Print current version and feature status."""
    from app.version import (
        __version__, __build_date__, __codename__,
        __author__, FEATURES, version_string
    )

    print(f"\n  {version_string()}")
    print(f"  Build date: {__build_date__}")
    print(f"  Author: {__author__}")
    print(f"\n  Features:")
    for feat, enabled in FEATURES.items():
        status = "\u2713" if enabled else "\u2717"
        print(f"    {status}  {feat}")
    print()


def show_history():
    """Print changelog contents."""
    if CHANGELOG_FILE.exists():
        print(CHANGELOG_FILE.read_text(encoding="utf-8"))
    else:
        print("No CHANGELOG.md found. Use 'python update.py changelog \"message\"' to start one.")


def prepare_release(bump_type: str = "patch", message: str | None = None):
    """Full release cycle: bump version, update changelog, print git commands."""
    old_version = read_version()
    new_version = bump_version(bump_type)

    release_msg = message or f"Release v{new_version}"
    add_changelog_entry(release_msg, new_version)

    print(f"\n  Release prepared: v{old_version} → v{new_version}")
    print(f"\n  Suggested git commands:")
    print(f"    git add -A")
    print(f"    git commit -m \"Release v{new_version}: {release_msg}\"")
    print(f"    git tag v{new_version}")
    print(f"    git push origin main --tags")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="DocView Update Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update.py status                     Show current version
  python update.py bump patch                 Bump patch version
  python update.py bump minor                 Bump minor version
  python update.py changelog "Added dark mode" Add changelog entry
  python update.py release minor "New features" Prepare minor release
  python update.py history                    Show changelog
        """
    )
    sub = parser.add_subparsers(dest="command")

    # Status
    sub.add_parser("status", help="Show current version and features")

    # Bump
    bump_p = sub.add_parser("bump", help="Bump version (patch/minor/major)")
    bump_p.add_argument("type", choices=["patch", "minor", "major"])

    # Changelog
    cl_p = sub.add_parser("changelog", help="Add a changelog entry")
    cl_p.add_argument("message", help="Changelog entry text")

    # Release
    rel_p = sub.add_parser("release", help="Prepare a release")
    rel_p.add_argument("type", nargs="?", default="patch",
                        choices=["patch", "minor", "major"])
    rel_p.add_argument("message", nargs="?", default=None)

    # History
    sub.add_parser("history", help="Show changelog")

    args = parser.parse_args()

    if args.command == "status":
        show_status()
    elif args.command == "bump":
        old = read_version()
        new = bump_version(args.type)
        print(f"  Version bumped: {old} → {new}")
    elif args.command == "changelog":
        add_changelog_entry(args.message)
    elif args.command == "release":
        prepare_release(args.type, args.message)
    elif args.command == "history":
        show_history()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
