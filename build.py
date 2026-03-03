#!/usr/bin/env python3
"""
DocView Build Script — Package into single executable using PyInstaller.

Usage:
    python build.py              # Build single executable
    python build.py --onedir     # Build as directory bundle (faster startup)
    python build.py --clean      # Clean build artifacts before building
"""

import subprocess
import sys
import os
import shutil
import argparse
import platform


APP_NAME = "DocView"
ENTRY_POINT = "main.py"
ICON = "assets/docview.ico"


def check_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def clean_build():
    """Remove previous build artifacts."""
    for d in ["build", "dist", "__pycache__"]:
        if os.path.exists(d):
            try:
                shutil.rmtree(d, ignore_errors=True)
                print(f"  Cleaned: {d}/")
            except Exception as e:
                print(f"  Warning: could not fully clean {d}/ ({e})")
    for f in [f"{APP_NAME}.spec"]:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"  Cleaned: {f}")
            except Exception as e:
                print(f"  Warning: could not remove {f} ({e})")


def build(onedir=False):
    """Build the executable."""
    check_pyinstaller()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--noconfirm",
    ]

    if onedir:
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")

    # Detect OS for windowed mode
    if platform.system() == "Windows":
        cmd.append("--windowed")  # No console on Windows
    elif platform.system() == "Darwin":
        cmd.append("--windowed")

    # Hidden imports that PyInstaller may miss
    hidden_imports = [
        "fitz",
        "fitz.fitz",
        "customtkinter",
        "tkinter",
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
    ]
    for hi in hidden_imports:
        cmd.extend(["--hidden-import", hi])

    # Include the app/ directory as data
    sep = ";" if platform.system() == "Windows" else ":"
    if os.path.exists("app"):
        cmd.extend(["--add-data", f"app{sep}app"])
    # Include assets (icon, etc.)
    if os.path.exists("assets"):
        cmd.extend(["--add-data", f"assets{sep}assets"])

    if ICON and os.path.exists(ICON):
        cmd.extend(["--icon", ICON])

    cmd.append(ENTRY_POINT)

    print(f"\nBuilding {APP_NAME}...")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        if onedir:
            output = os.path.join("dist", APP_NAME)
        else:
            ext = ".exe" if platform.system() == "Windows" else ""
            output = os.path.join("dist", f"{APP_NAME}{ext}")

        print(f"\n{'='*50}")
        print(f"BUILD SUCCESSFUL")
        print(f"Output: {output}")
        print(f"{'='*50}")

        # Size info
        if os.path.exists(output):
            if os.path.isfile(output):
                size_mb = os.path.getsize(output) / (1024 * 1024)
                print(f"Size: {size_mb:.1f} MB")
            else:
                total = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, dn, fn in os.walk(output)
                    for f in fn
                )
                print(f"Size: {total / (1024*1024):.1f} MB (directory)")
    else:
        print("\nBUILD FAILED")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME} executable")
    parser.add_argument("--onedir", action="store_true", help="Build as directory instead of single file")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts first")
    args = parser.parse_args()

    print(f"=== {APP_NAME} Build System ===")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    print()

    if args.clean:
        print("Cleaning build artifacts...")
        clean_build()
        print()

    build(onedir=args.onedir)


if __name__ == "__main__":
    main()
