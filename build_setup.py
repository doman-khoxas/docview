#!/usr/bin/env python3
"""
DocSetup Build — Builds DocView + DocNotes and compiles the combined installer.

Usage:
    python build_setup.py              # Build both apps + installer
    python build_setup.py --clean      # Clean first, then build
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


def find_iscc() -> str | None:
    result = shutil.which("ISCC")
    if result:
        return result
    for p in ISCC_PATHS:
        if os.path.isfile(p):
            return p
    return None


def run(desc: str, cmd: list[str]):
    print(f"\n  {desc}...")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  FAILED: {desc}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Build DocView + DocNotes + combined installer")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    print("=" * 55)
    print("  DocSetup — Combined Build System")
    print(f"  Platform: {platform.system()} {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]}")
    print("=" * 55)

    iscc = find_iscc()
    if not iscc:
        print("\n  ERROR: Inno Setup not found.")
        print("  Install: winget install JRSoftware.InnoSetup")
        sys.exit(1)

    py = sys.executable

    if args.clean:
        print("\nCleaning...")
        for d in ["build", "dist"]:
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)
                print(f"  Cleaned: {d}/")
        for f in ["DocView.spec", "DocNotes.spec"]:
            if os.path.exists(f):
                os.remove(f)

    # Step 1: Build DocView (onedir)
    run("Step 1/3: Building DocView",
        [py, "build.py", "--onedir"])

    # Step 2: Build DocNotes (onedir)
    run("Step 2/3: Building DocNotes",
        [py, "build_docnotes.py", "--onedir"])

    # Step 3: Compile combined installer
    print(f"\n  Step 3/3: Compiling DocSetup installer...")
    result = subprocess.run([iscc, "installer_setup.iss"])
    if result.returncode != 0:
        print("  INSTALLER FAILED")
        sys.exit(1)

    # Report
    for f in os.listdir("."):
        if f.startswith("DocSetup_") and f.endswith(".exe"):
            size_mb = os.path.getsize(f) / (1024 * 1024)
            print(f"\n  INSTALLER: {f} ({size_mb:.1f} MB)")

    print(f"\n{'=' * 55}")
    print("  BUILD COMPLETE")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
