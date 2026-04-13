#!/usr/bin/env python3
"""
DocNotes Build Script — Package into executable using PyInstaller.

Usage:
    python build_docnotes.py              # Build single executable
    python build_docnotes.py --onedir     # Build as directory bundle
    python build_docnotes.py --clean      # Clean build artifacts first

Run from the project root (docview/), not from docnotes/.
"""
import subprocess
import sys
import os
import shutil
import argparse
import platform

APP_NAME = "DocNotes"
ENTRY_POINT = os.path.join("docnotes", "docnotes.py")
ICON = os.path.join("assets", "docnotes_icon.ico")


def check_pyinstaller():
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def clean_build():
    for d in ["build", f"dist/{APP_NAME}", "__pycache__"]:
        if os.path.exists(d):
            try:
                shutil.rmtree(d, ignore_errors=True)
                print(f"  Cleaned: {d}/")
            except Exception as e:
                print(f"  WARNING: Could not fully clean {d}: {e}")
    for f in [f"{APP_NAME}.spec"]:
        if os.path.exists(f):
            os.remove(f)
            print(f"  Cleaned: {f}")


def build(onedir=False):
    check_pyinstaller()

    if not os.path.exists(ENTRY_POINT):
        print(f"  ERROR: {ENTRY_POINT} not found.")
        print(f"  Run this script from the project root (docview/), not from docnotes/.")
        sys.exit(1)

    sep = ";" if platform.system() == "Windows" else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--noconfirm",
        "--onedir" if onedir else "--onefile",
    ]

    if platform.system() in ("Windows", "Darwin"):
        cmd.append("--windowed")

    # Data files
    for src in ["app", "docnotes", "assets"]:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src}{sep}{src}"])

    # Icon
    if os.path.exists(ICON):
        cmd.extend(["--icon", ICON])

    # Hidden imports
    for hi in [
        "fitz", "fitz.fitz",
        "PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui",
        "PIL", "PIL.Image",
        "markdown", "yaml",
        "markdown.extensions", "markdown.extensions.tables",
        "markdown.extensions.fenced_code", "markdown.extensions.toc",
        "markdown.extensions.nl2br", "markdown.extensions.sane_lists",
        "markdown.extensions.meta", "markdown.extensions.codehilite",
    ]:
        cmd.extend(["--hidden-import", hi])

    cmd.append(ENTRY_POINT)

    print(f"\n  Building {APP_NAME} ({'directory' if onedir else 'single file'})...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        if onedir:
            output = os.path.join("dist", APP_NAME)
        else:
            ext = ".exe" if platform.system() == "Windows" else ""
            output = os.path.join("dist", f"{APP_NAME}{ext}")

        if os.path.exists(output):
            if os.path.isfile(output):
                size_mb = os.path.getsize(output) / (1024 * 1024)
                print(f"\n  Output: {output} ({size_mb:.1f} MB)")
            else:
                total = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, dn, fn in os.walk(output) for f in fn
                )
                print(f"\n  Output: {output} ({total / (1024 * 1024):.1f} MB)")
    else:
        print("\n  BUILD FAILED")
        sys.exit(1)


INNO_PATHS = [
    r"C:\Users\gt8le\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
]
INSTALLER_SCRIPT = "installer_docnotes.iss"


def find_inno_setup() -> str | None:
    result = shutil.which("ISCC")
    if result:
        return result
    for path in INNO_PATHS:
        if os.path.isfile(path):
            return path
    return None


def build_installer():
    iscc = find_inno_setup()
    if not iscc:
        print("\n  ERROR: Inno Setup not found.")
        print("  Install: winget install JRSoftware.InnoSetup")
        sys.exit(1)

    if not os.path.exists(os.path.join("dist", APP_NAME)):
        print(f"  ERROR: dist/{APP_NAME}/ not found. Run --onedir first.")
        sys.exit(1)

    print(f"\n  Compiling installer with {iscc}...")
    result = subprocess.run([iscc, INSTALLER_SCRIPT])
    if result.returncode == 0:
        for f in os.listdir("."):
            if f.startswith("DocNotes_") and f.endswith("_Setup.exe"):
                size_mb = os.path.getsize(f) / (1024 * 1024)
                print(f"\n  INSTALLER: {f} ({size_mb:.1f} MB)")
                return
    else:
        print("  INSTALLER BUILD FAILED")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME} executable")
    parser.add_argument("--onedir", action="store_true",
                        help="Build as directory bundle")
    parser.add_argument("--clean", action="store_true",
                        help="Clean build artifacts first")
    parser.add_argument("--installer", action="store_true",
                        help="Build directory bundle + Windows installer (requires Inno Setup)")
    args = parser.parse_args()

    print(f"{'=' * 50}")
    print(f"  {APP_NAME} Build System")
    print(f"  Platform: {platform.system()} {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"{'=' * 50}")

    if args.clean:
        print("\nCleaning...")
        clean_build()

    if args.installer:
        print("\nStep 1/2: Building application...")
        build(onedir=True)
        print("\nStep 2/2: Building installer...")
        build_installer()
    else:
        print("\nBuilding...")
        build(onedir=args.onedir)

    print(f"\n{'=' * 50}")
    print(f"  BUILD COMPLETE")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
