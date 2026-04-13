#!/usr/bin/env python3
"""
DocSetup Build System
=====================
Builds DocView, DocNotes, or both, with optional Inno Setup installer.

Usage:
    python build_setup.py                  # Build both apps + combined installer
    python build_setup.py --docview        # Build DocView only
    python build_setup.py --docnotes       # Build DocNotes only
    python build_setup.py --no-installer   # Build apps without installer
    python build_setup.py --clean          # Clean first
"""
import subprocess
import sys
import os
import shutil
import argparse
import platform

ISCC_PATHS = [
    r"C:\Users\gt8le\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
]

HIDDEN_IMPORTS = [
    "fitz", "fitz.fitz",
    "PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui",
    "PIL", "PIL.Image",
    "markdown", "yaml",
    "markdown.extensions", "markdown.extensions.tables",
    "markdown.extensions.fenced_code", "markdown.extensions.toc",
    "markdown.extensions.nl2br", "markdown.extensions.sane_lists",
    "markdown.extensions.meta", "markdown.extensions.codehilite",
]


def find_iscc() -> str | None:
    result = shutil.which("ISCC")
    if result:
        return result
    for p in ISCC_PATHS:
        if os.path.isfile(p):
            return p
    return None


def clean():
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
            print(f"  Cleaned: {d}/")
    for f in ["DocView.spec", "DocNotes.spec"]:
        if os.path.exists(f):
            os.remove(f)
    for f in os.listdir("."):
        if f.endswith("_Setup.exe") or (f.startswith("DocSetup_") and f.endswith(".exe")):
            os.remove(f)
            print(f"  Cleaned: {f}")


def build_app(name: str, entry_point: str, icon: str, data_dirs: list[str]):
    """Build a single app with PyInstaller --onedir."""
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    sep = ";" if platform.system() == "Windows" else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", name,
        "--noconfirm",
        "--onedir",
    ]

    if platform.system() in ("Windows", "Darwin"):
        cmd.append("--windowed")

    for hi in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hi])

    for d in data_dirs:
        if os.path.exists(d):
            cmd.extend(["--add-data", f"{d}{sep}{d}"])

    if os.path.exists(icon):
        cmd.extend(["--icon", icon])

    cmd.append(entry_point)

    print(f"  Building {name}...")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  FAILED: {name}")
        sys.exit(1)

    output = os.path.join("dist", name)
    if os.path.exists(output):
        total = sum(
            os.path.getsize(os.path.join(dp, f))
            for dp, dn, fn in os.walk(output) for f in fn
        )
        print(f"  Output: {output} ({total / (1024 * 1024):.1f} MB)")


def main():
    parser = argparse.ArgumentParser(
        description="DocSetup Build System — DocView + DocNotes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--docview", action="store_true", help="Build DocView only")
    parser.add_argument("--docnotes", action="store_true", help="Build DocNotes only")
    parser.add_argument("--no-installer", action="store_true", help="Skip installer compilation")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts first")
    args = parser.parse_args()

    # Default: build both
    build_dv = not args.docnotes or args.docview
    build_dn = not args.docview or args.docnotes
    if not args.docview and not args.docnotes:
        build_dv = build_dn = True

    print("=" * 55)
    print("  DocSetup Build System")
    print(f"  Platform: {platform.system()} {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Build: {'DocView' if build_dv else ''} {'DocNotes' if build_dn else ''}")
    print("=" * 55)

    if args.clean:
        print("\nCleaning...")
        clean()

    step = 0
    total_steps = int(build_dv) + int(build_dn) + (0 if args.no_installer else 1)

    if build_dv:
        step += 1
        print(f"\nStep {step}/{total_steps}: DocView")
        build_app("DocView", "docview.py", os.path.join("assets", "icon.ico"),
                   ["app", "assets"])

    if build_dn:
        step += 1
        print(f"\nStep {step}/{total_steps}: DocNotes")
        build_app("DocNotes", os.path.join("docnotes", "docnotes.py"),
                   os.path.join("assets", "docnotes_icon.ico"),
                   ["app", "docnotes", "assets"])

    if not args.no_installer:
        step += 1
        iscc = find_iscc()
        if not iscc:
            print(f"\n  WARNING: Inno Setup not found — skipping installer.")
            print("  Install: winget install JRSoftware.InnoSetup")
        else:
            print(f"\nStep {step}/{total_steps}: Compiling installer")
            result = subprocess.run([iscc, "installer_setup.iss"])
            if result.returncode != 0:
                print("  INSTALLER FAILED")
                sys.exit(1)
            for f in os.listdir("."):
                if f.startswith("DocSetup_") and f.endswith(".exe"):
                    size_mb = os.path.getsize(f) / (1024 * 1024)
                    print(f"\n  INSTALLER: {f} ({size_mb:.1f} MB)")

    print(f"\n{'=' * 55}")
    print("  BUILD COMPLETE")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
