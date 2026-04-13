#!/usr/bin/env python3
"""
DocView Build System
====================

Usage:
    python build.py                    # Build single executable
    python build.py --onedir           # Build as directory bundle (for installer)
    python build.py --clean            # Clean build artifacts before building
    python build.py --installer        # Build directory bundle + Inno Setup installer
    python build.py --icon             # Regenerate icon files only

The installer requires Inno Setup 6 to be installed:
  https://jrsoftware.org/isdl.php
"""
import subprocess
import sys
import os
import shutil
import argparse
import platform

from app.version import APP_NAME, __version__

ENTRY_POINT = "docview.py"
ICON = os.path.join("assets", "icon.ico")
INSTALLER_SCRIPT = "installer.iss"

# Inno Setup default install locations
INNO_PATHS = [
    r"C:\Users\gt8le\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
]


def check_pyinstaller():
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("  Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def find_inno_setup() -> str | None:
    """Find Inno Setup compiler (ISCC.exe)."""
    # Check PATH first
    result = shutil.which("ISCC")
    if result:
        return result
    # Check common install locations
    for path in INNO_PATHS:
        if os.path.isfile(path):
            return path
    return None


def clean_build():
    """Remove previous build artifacts."""
    for d in ["build", "dist", "__pycache__"]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"  Cleaned: {d}/")
    for f in [f"{APP_NAME}.spec"]:
        if os.path.exists(f):
            os.remove(f)
            print(f"  Cleaned: {f}")
    # Clean installer output
    for f in os.listdir("."):
        if f.startswith("DocView_") and f.endswith("_Setup.exe"):
            os.remove(f)
            print(f"  Cleaned: {f}")


def generate_icon():
    """Regenerate icon files from assets/generate_icon.py."""
    gen_script = os.path.join("assets", "generate_icon.py")
    if not os.path.exists(gen_script):
        print("  ERROR: assets/generate_icon.py not found")
        return False
    result = subprocess.run([sys.executable, gen_script])
    return result.returncode == 0


def build_app(onedir=False):
    """Build the application with PyInstaller."""
    check_pyinstaller()

    # Ensure icon exists
    if not os.path.exists(ICON):
        print("\n  Icon not found, generating...")
        generate_icon()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--noconfirm",
    ]

    if onedir:
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")

    if platform.system() in ("Windows", "Darwin"):
        cmd.append("--windowed")

    hidden_imports = [
        "fitz", "fitz.fitz",
        "PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui",
        "PIL", "PIL.Image",
        "markdown", "yaml",
        "markdown.extensions", "markdown.extensions.tables",
        "markdown.extensions.fenced_code", "markdown.extensions.toc",
        "markdown.extensions.nl2br", "markdown.extensions.sane_lists",
        "markdown.extensions.meta", "markdown.extensions.codehilite",
    ]
    for hi in hidden_imports:
        cmd.extend(["--hidden-import", hi])

    # Include app package
    if os.path.exists("app"):
        sep = ";" if platform.system() == "Windows" else ":"
        cmd.extend(["--add-data", f"app{sep}app"])

    # Include assets
    if os.path.exists("assets"):
        sep = ";" if platform.system() == "Windows" else ":"
        cmd.extend(["--add-data", f"assets{sep}assets"])

    # Include icon
    if os.path.exists(ICON):
        cmd.extend(["--icon", ICON])

    cmd.append(ENTRY_POINT)

    print(f"\n  Building {APP_NAME} ({'directory' if onedir else 'single file'})...")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("\n  BUILD FAILED")
        sys.exit(1)

    if onedir:
        output = os.path.join("dist", APP_NAME)
    else:
        ext = ".exe" if platform.system() == "Windows" else ""
        output = os.path.join("dist", f"{APP_NAME}{ext}")

    if os.path.exists(output):
        if os.path.isfile(output):
            size_mb = os.path.getsize(output) / (1024 * 1024)
            print(f"  Output: {output} ({size_mb:.1f} MB)")
        else:
            total = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, dn, fn in os.walk(output)
                for f in fn
            )
            print(f"  Output: {output} ({total / (1024 * 1024):.1f} MB directory)")

    return output


def build_installer():
    """Build Inno Setup installer from the onedir output."""
    iscc = find_inno_setup()
    if not iscc:
        print("\n  ERROR: Inno Setup not found.")
        print("  Install from: https://jrsoftware.org/isdl.php")
        print("  Or add ISCC.exe to your PATH.")
        sys.exit(1)

    print(f"\n  Inno Setup: {iscc}")

    if not os.path.exists(INSTALLER_SCRIPT):
        print(f"  ERROR: {INSTALLER_SCRIPT} not found")
        sys.exit(1)

    # Verify the dist directory exists
    dist_dir = os.path.join("dist", APP_NAME)
    if not os.path.exists(dist_dir):
        print(f"  ERROR: {dist_dir} not found. Run build --onedir first.")
        sys.exit(1)

    print(f"  Compiling installer...")
    result = subprocess.run([iscc, INSTALLER_SCRIPT])

    if result.returncode == 0:
        # Find the output .exe
        for f in os.listdir("."):
            if f.startswith("DocView_") and f.endswith("_Setup.exe"):
                size_mb = os.path.getsize(f) / (1024 * 1024)
                print(f"\n  INSTALLER: {f} ({size_mb:.1f} MB)")
                return f
        print("  Installer compiled (check output directory)")
    else:
        print("  INSTALLER BUILD FAILED")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} Build System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--onedir", action="store_true",
                        help="Build as directory bundle (required for installer)")
    parser.add_argument("--clean", action="store_true",
                        help="Clean build artifacts first")
    parser.add_argument("--installer", action="store_true",
                        help="Build directory bundle + Windows installer (requires Inno Setup)")
    parser.add_argument("--icon", action="store_true",
                        help="Regenerate icon files only")
    args = parser.parse_args()

    print(f"{'=' * 55}")
    print(f"  {APP_NAME} v{__version__} Build System")
    print(f"  Platform: {platform.system()} {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"{'=' * 55}")

    if args.icon:
        print("\nRegenerating icons...")
        generate_icon()
        return

    if args.clean:
        print("\nCleaning...")
        clean_build()

    if args.installer:
        # Installer requires onedir build
        print("\nStep 1/2: Building application (directory bundle)...")
        build_app(onedir=True)
        print("\nStep 2/2: Building installer...")
        build_installer()
    else:
        print("\nBuilding application...")
        output = build_app(onedir=args.onedir)

    print(f"\n{'=' * 55}")
    print(f"  BUILD COMPLETE")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
