"""CLI mode for headless document operations.

Supports PDF operations (redact, OCR, text extraction) and
Markdown combine (merge multiple .md files into one with TOC).
"""
import sys
import os
import re
import glob
import argparse
from pathlib import Path
from app.version import APP_NAME, __version__
from app.core.pdf_engine import PDFEngine, HAS_FITZ


def run_cli(args):
    """CLI mode for headless PDF operations."""
    if not HAS_FITZ:
        print("ERROR: PyMuPDF required. Run: pip install PyMuPDF")
        sys.exit(1)

    engine = PDFEngine(args.input)
    print(f"Loaded: {args.input} ({engine.page_count()} pages)")

    # Redaction
    if args.redact:
        for spec in args.redact:
            parts = dict(item.split(":") for item in spec.split(","))
            page = int(parts.get("page", 1)) - 1
            x = float(parts.get("x", 0))
            y = float(parts.get("y", 0))
            w = float(parts.get("w", 100))
            h = float(parts.get("h", 20))
            engine.redact_area(page, x, y, w, h)
            print(f"  Redacted area on page {page + 1}: ({x},{y}) {w}x{h}")

    if args.redact_text:
        for spec in args.redact_text:
            parts = spec.split(":", 1)
            if len(parts) == 2:
                page = int(parts[0]) - 1
                text = parts[1]
            else:
                text = parts[0]
                for p in range(engine.page_count()):
                    count = engine.redact_text(p, text)
                    if count:
                        print(f"  Redacted '{text}' on page {p + 1}: {count} occurrences")
                text = None
            if text:
                count = engine.redact_text(page, text)
                print(f"  Redacted '{text}' on page {page + 1}: {count} occurrences")

    # OCR
    if args.ocr:
        print("Running OCR...")
        try:
            result = engine.ocr_document(
                args.output,
                language=args.lang or "eng",
                deskew=not args.no_deskew,
                force=args.force_ocr
            )
            print(f"OCR output: {result}")
            engine.close()
            return
        except Exception as e:
            print(f"OCR Error: {e}")
            sys.exit(1)

    # Extract text
    if args.extract_text:
        if args.extract_text == "all":
            print(engine.get_all_text())
        else:
            page = int(args.extract_text) - 1
            print(engine.get_text(page))
        engine.close()
        return

    # Save
    output = args.output or args.input
    engine.save(output)
    print(f"Saved: {output}")
    engine.close()


# ─── Markdown Combine ────────────────────────────────────────────


def _strip_yaml_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (--- ... ---) from the top of a markdown file."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].lstrip("\n")
    return text


def _resolve_file_list(paths: list[str]) -> list[Path]:
    """Expand globs and resolve paths. Returns list of existing .md files."""
    resolved = []
    for p in paths:
        matches = glob.glob(p, recursive=True)
        if matches:
            for m in sorted(matches):
                mp = Path(m)
                if mp.is_file():
                    resolved.append(mp)
        else:
            # Treat as literal path
            pp = Path(p)
            if pp.is_file():
                resolved.append(pp)
            else:
                print(f"WARNING: File not found: {p}")
    return resolved


def _combine_files(
    files: list[Path],
    toc: bool = True,
    strip_frontmatter: bool = False,
    separator: str = "\n---\n\n",
) -> str:
    """Combine multiple markdown files into a single document."""
    sections = []
    toc_entries = []

    for f in files:
        content = f.read_text(encoding="utf-8")
        if strip_frontmatter:
            content = _strip_yaml_frontmatter(content)

        name = f.stem
        toc_entries.append(f"- [{name}](#{name.lower().replace(' ', '-')})")
        section = f"<!-- source: {f} -->\n# {name}\n\n{content.strip()}"
        sections.append(section)

    parts = []
    if toc and len(files) > 1:
        parts.append("# Table of Contents\n")
        parts.append("\n".join(toc_entries))
        parts.append(separator)

    parts.append(separator.join(sections))
    parts.append("")  # trailing newline
    return "\n".join(parts)


def run_combine(args):
    """CLI handler for --combine: merge multiple .md files into one."""
    files = _resolve_file_list(args.combine)
    if not files:
        print("ERROR: No files found to combine.")
        sys.exit(1)

    output = args.output
    if not output:
        print("ERROR: --combine requires --output/-o")
        sys.exit(1)

    toc = not args.no_toc
    result = _combine_files(
        files,
        toc=toc,
        strip_frontmatter=args.strip_frontmatter,
        separator=args.separator or "\n---\n\n",
    )

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(result, encoding="utf-8")
    print(f"Combined {len(files)} files -> {output}")


def run_combine_manifest(args):
    """CLI handler for --combine-manifest: build bundles from a YAML manifest."""
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML required for manifest mode. Run: pip install pyyaml")
        sys.exit(1)

    manifest_path = Path(args.combine_manifest)
    if not manifest_path.is_file():
        print(f"ERROR: Manifest not found: {manifest_path}")
        sys.exit(1)

    with open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    base_dir = manifest_path.parent
    output_dir = base_dir / manifest.get("output_dir", ".")
    output_dir.mkdir(parents=True, exist_ok=True)

    global_strip = manifest.get("strip_frontmatter", False)
    global_toc = manifest.get("toc", True)
    separator = manifest.get("separator", "\n---\n\n")

    bundles = manifest.get("bundles", [])
    if not bundles:
        print("WARNING: No bundles defined in manifest.")
        return

    # Resolve file paths relative to manifest's base_dir or source_root
    source_root = base_dir / manifest.get("source_root", ".")

    for bundle in bundles:
        name = bundle.get("name", "unnamed")
        out_file = output_dir / bundle["output"]
        raw_files = bundle.get("files", [])
        strip = bundle.get("strip_frontmatter", global_strip)
        toc = bundle.get("toc", global_toc)

        # Resolve paths relative to source_root
        resolved_paths = []
        for p in raw_files:
            full = str(source_root / p)
            resolved_paths.append(full)

        files = _resolve_file_list(resolved_paths)
        if not files:
            print(f"  SKIP [{name}] — no files found")
            continue

        result = _combine_files(files, toc=toc, strip_frontmatter=strip, separator=separator)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(result, encoding="utf-8")
        print(f"  [{name}] {len(files)} files -> {out_file}")

    # Handle copy directives
    copies = manifest.get("copies", [])
    for copy_item in copies:
        src = source_root / copy_item["source"]
        dst = output_dir / copy_item["output"]
        if not src.is_file():
            print(f"  SKIP copy [{copy_item.get('name', src)}] — source not found: {src}")
            continue
        content = src.read_text(encoding="utf-8")
        if copy_item.get("strip_frontmatter", global_strip):
            content = _strip_yaml_frontmatter(content)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8")
        print(f"  [{copy_item.get('name', dst.stem)}] copied -> {dst}")

    print(f"\nManifest build complete: {output_dir}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} v{__version__} -- Document Viewer & Editor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  GUI Mode:
    python docview.py
    python docview.py document.pdf
    python docview.py notes.md

  CLI Redaction:
    python docview.py --cli -i doc.pdf --redact "page:1,x:50,y:100,w:200,h:30" -o redacted.pdf
    python docview.py --cli -i doc.pdf --redact-text "SSN" -o redacted.pdf

  CLI OCR:
    python docview.py --cli -i scanned.pdf --ocr -o searchable.pdf

  CLI Text Extract:
    python docview.py --cli -i doc.pdf --extract-text all
        """
    )

    parser.add_argument("file", nargs="?", help="File to open (GUI mode)")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode (no GUI)")
    parser.add_argument("-i", "--input", help="Input PDF file (CLI mode)")
    parser.add_argument("-o", "--output", help="Output PDF file")
    parser.add_argument("--redact", nargs="+", help='Redact areas: "page:1,x:50,y:100,w:200,h:30"')
    parser.add_argument("--redact-text", nargs="+", help='Redact text: "text" or "page:text"')
    parser.add_argument("--ocr", action="store_true", help="Run OCR on document")
    parser.add_argument("--lang", default="eng", help="OCR language (default: eng)")
    parser.add_argument("--no-deskew", action="store_true", help="Disable deskew during OCR")
    parser.add_argument("--force-ocr", action="store_true", help="Force OCR even if text exists")
    parser.add_argument("--extract-text", help='Extract text: "all" or page number')
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")

    # Markdown combine
    parser.add_argument("--combine", nargs="+", metavar="FILE",
                        help="Combine multiple .md files into one (supports globs)")
    parser.add_argument("--combine-manifest", metavar="YAML",
                        help="Build bundles from a YAML manifest file")
    parser.add_argument("--no-toc", action="store_true",
                        help="Disable table of contents in combined output")
    parser.add_argument("--strip-frontmatter", action="store_true",
                        help="Remove YAML frontmatter from source files")
    parser.add_argument("--separator", default=None,
                        help='Separator between files (default: "---")')

    return parser
