#!/usr/bin/env python3
"""
DocView File Association Installer for Windows.

Registers DocView as a PDF file handler so you can:
  - Set DocView as your default PDF application
  - Right-click any PDF → "Open with DocView"
  - Double-click PDFs to open them in DocView

Usage:
    python install.py               # Install (current user)
    python install.py --system      # Install (all users — requires admin)
    python install.py --uninstall   # Remove file associations
    python install.py --status      # Show current registration status

The installer detects whether you're running from source (main.py) or
from a built executable (DocView.exe) and registers accordingly.
"""

import os
import sys
import argparse
import platform
import ctypes
import shutil

APP_NAME = "DocView"
APP_ID = "DocView.PDF.Viewer"
FILE_EXT = ".pdf"
PROG_ID = "DocView.PDF.1"
DESCRIPTION = "DocView PDF Document"
ICON_NAME = "docview.ico"


def is_admin() -> bool:
    """Check if running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_app_path() -> str:
    """Detect the executable or script path to register."""
    base = os.path.dirname(os.path.abspath(__file__))

    # Check for built executable first
    exe_path = os.path.join(base, "dist", "DocView.exe")
    if os.path.exists(exe_path):
        return exe_path

    # Check if running as frozen exe
    if getattr(sys, 'frozen', False):
        return sys.executable

    # Fall back to script-based launch via pythonw
    main_py = os.path.join(base, "main.py")
    if os.path.exists(main_py):
        # Find pythonw.exe (no console window) or python.exe
        python_dir = os.path.dirname(sys.executable)
        pythonw = os.path.join(python_dir, "pythonw.exe")
        if os.path.exists(pythonw):
            return pythonw
        return sys.executable
    return sys.executable


def get_launch_command(app_path: str) -> str:
    """Build the shell command that opens a PDF with DocView."""
    base = os.path.dirname(os.path.abspath(__file__))

    if app_path.endswith(".exe") and "python" not in app_path.lower():
        # Built executable — direct invocation
        return f'"{app_path}" "%1"'
    else:
        # Script mode — python[w].exe main.py <file>
        main_py = os.path.join(base, "main.py")
        return f'"{app_path}" "{main_py}" "%1"'


def get_icon_path() -> str:
    """Find the .ico file."""
    base = os.path.dirname(os.path.abspath(__file__))
    ico = os.path.join(base, "assets", ICON_NAME)
    if os.path.exists(ico):
        return ico
    return ""


def install_user():
    """Register DocView for the current user (no admin required)."""
    import winreg

    app_path = get_app_path()
    command = get_launch_command(app_path)
    icon_path = get_icon_path()

    print(f"  App path:  {app_path}")
    print(f"  Command:   {command}")
    print(f"  Icon:      {icon_path or '(none)'}")
    print()

    # --- Register ProgId under HKCU\Software\Classes ---
    prog_key = rf"Software\Classes\{PROG_ID}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, prog_key) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, DESCRIPTION)

    # Default icon
    if icon_path:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{prog_key}\DefaultIcon") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{icon_path}",0')

    # Shell open command
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{prog_key}\shell\open\command") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

    # Friendly app name
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{prog_key}\shell\open") as key:
        winreg.SetValueEx(key, "FriendlyAppName", 0, winreg.REG_SZ, APP_NAME)

    # --- Register the .pdf extension handler ---
    ext_key = rf"Software\Classes\{FILE_EXT}\OpenWithProgids"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, ext_key) as key:
        winreg.SetValueEx(key, PROG_ID, 0, winreg.REG_NONE, b"")

    # --- Register in Applications list ---
    app_reg = rf"Software\Classes\Applications\DocView.exe"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, app_reg) as key:
        winreg.SetValueEx(key, "FriendlyAppName", 0, winreg.REG_SZ, APP_NAME)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{app_reg}\shell\open\command") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
    if icon_path:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{app_reg}\DefaultIcon") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{icon_path}",0')

    # --- Register App User Model ID for Start Menu / Taskbar ---
    cap_key = rf"Software\{APP_NAME}\Capabilities"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cap_key) as key:
        winreg.SetValueEx(key, "ApplicationName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "ApplicationDescription", 0, winreg.REG_SZ,
                          "Professional PDF viewer, editor, and annotator")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{cap_key}\FileAssociations") as key:
        winreg.SetValueEx(key, FILE_EXT, 0, winreg.REG_SZ, PROG_ID)

    # Register application capabilities
    reg_apps = r"Software\RegisteredApplications"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_apps) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cap_key)

    # Notify Windows of the change
    _notify_shell()
    print("  [OK] DocView registered as PDF handler for current user.")
    print()
    print("  To set as default:")
    print("    1. Open Windows Settings > Default Apps")
    print("    2. Search for '.pdf'")
    print("    3. Select 'DocView' from the list")
    print()
    print("  Or right-click any PDF > Open With > DocView")


def install_system():
    """Register DocView for all users (requires admin)."""
    import winreg

    if not is_admin():
        print("  [ERROR] System-wide install requires administrator privileges.")
        print("  Run this script as Administrator or use: python install.py (no --system)")
        sys.exit(1)

    app_path = get_app_path()
    command = get_launch_command(app_path)
    icon_path = get_icon_path()

    print(f"  App path:  {app_path}")
    print(f"  Command:   {command}")
    print(f"  Icon:      {icon_path or '(none)'}")
    print()

    # ProgId under HKLM
    prog_key = rf"Software\Classes\{PROG_ID}"
    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, prog_key) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, DESCRIPTION)

    if icon_path:
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, rf"{prog_key}\DefaultIcon") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'"{icon_path}",0')

    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, rf"{prog_key}\shell\open\command") as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, rf"{prog_key}\shell\open") as key:
        winreg.SetValueEx(key, "FriendlyAppName", 0, winreg.REG_SZ, APP_NAME)

    # .pdf OpenWithProgids
    ext_key = rf"Software\Classes\{FILE_EXT}\OpenWithProgids"
    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, ext_key) as key:
        winreg.SetValueEx(key, PROG_ID, 0, winreg.REG_NONE, b"")

    # Application capabilities
    cap_key = rf"Software\{APP_NAME}\Capabilities"
    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, cap_key) as key:
        winreg.SetValueEx(key, "ApplicationName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "ApplicationDescription", 0, winreg.REG_SZ,
                          "Professional PDF viewer, editor, and annotator")
    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, rf"{cap_key}\FileAssociations") as key:
        winreg.SetValueEx(key, FILE_EXT, 0, winreg.REG_SZ, PROG_ID)

    reg_apps = r"Software\RegisteredApplications"
    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_apps) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cap_key)

    _notify_shell()
    print("  [OK] DocView registered system-wide as PDF handler.")
    print()
    print("  To set as default:")
    print("    1. Open Windows Settings > Default Apps")
    print("    2. Search for '.pdf'")
    print("    3. Select 'DocView' from the list")


def uninstall():
    """Remove all DocView file association registry entries."""
    import winreg

    removed = 0
    # Keys to remove from HKCU
    hkcu_keys = [
        rf"Software\Classes\{PROG_ID}\shell\open\command",
        rf"Software\Classes\{PROG_ID}\shell\open",
        rf"Software\Classes\{PROG_ID}\shell",
        rf"Software\Classes\{PROG_ID}\DefaultIcon",
        rf"Software\Classes\{PROG_ID}",
        rf"Software\Classes\Applications\DocView.exe\shell\open\command",
        rf"Software\Classes\Applications\DocView.exe\shell\open",
        rf"Software\Classes\Applications\DocView.exe\shell",
        rf"Software\Classes\Applications\DocView.exe\DefaultIcon",
        rf"Software\Classes\Applications\DocView.exe",
        rf"Software\{APP_NAME}\Capabilities\FileAssociations",
        rf"Software\{APP_NAME}\Capabilities",
        rf"Software\{APP_NAME}",
    ]

    for key_path in hkcu_keys:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            removed += 1
        except FileNotFoundError:
            pass
        except PermissionError:
            print(f"  [WARN] Cannot delete: HKCU\\{key_path}")

    # Remove ProgId from .pdf OpenWithProgids
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            rf"Software\Classes\{FILE_EXT}\OpenWithProgids",
                            0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, PROG_ID)
            removed += 1
    except (FileNotFoundError, OSError):
        pass

    # Remove from RegisteredApplications
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\RegisteredApplications",
                            0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
            removed += 1
    except (FileNotFoundError, OSError):
        pass

    # Also try HKLM if admin
    if is_admin():
        hklm_keys = [
            rf"Software\Classes\{PROG_ID}\shell\open\command",
            rf"Software\Classes\{PROG_ID}\shell\open",
            rf"Software\Classes\{PROG_ID}\shell",
            rf"Software\Classes\{PROG_ID}\DefaultIcon",
            rf"Software\Classes\{PROG_ID}",
            rf"Software\{APP_NAME}\Capabilities\FileAssociations",
            rf"Software\{APP_NAME}\Capabilities",
            rf"Software\{APP_NAME}",
        ]
        for key_path in hklm_keys:
            try:
                winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                removed += 1
            except (FileNotFoundError, PermissionError):
                pass
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                rf"Software\Classes\{FILE_EXT}\OpenWithProgids",
                                0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, PROG_ID)
                removed += 1
        except (FileNotFoundError, OSError):
            pass
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"Software\RegisteredApplications",
                                0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, APP_NAME)
                removed += 1
        except (FileNotFoundError, OSError):
            pass

    _notify_shell()

    if removed > 0:
        print(f"  [OK] Removed {removed} registry entries.")
        print("  DocView is no longer registered as a PDF handler.")
    else:
        print("  [INFO] No DocView file associations found to remove.")


def show_status():
    """Display current registration status."""
    import winreg

    print(f"  App path detected: {get_app_path()}")
    print()

    checks = [
        ("ProgId", winreg.HKEY_CURRENT_USER, rf"Software\Classes\{PROG_ID}"),
        ("Open command", winreg.HKEY_CURRENT_USER,
         rf"Software\Classes\{PROG_ID}\shell\open\command"),
        ("Capabilities", winreg.HKEY_CURRENT_USER,
         rf"Software\{APP_NAME}\Capabilities"),
        ("RegisteredApps", winreg.HKEY_CURRENT_USER,
         r"Software\RegisteredApplications"),
    ]

    for label, hive, key_path in checks:
        try:
            with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, "" if "RegisteredApps" not in key_path else APP_NAME)
                print(f"  [OK] {label}: {val}")
        except FileNotFoundError:
            print(f"  [--] {label}: Not registered")
        except Exception as e:
            print(f"  [??] {label}: {e}")

    # Check if DocView is the default handler
    print()
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            rf"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\{FILE_EXT}\UserChoice",
                            0, winreg.KEY_READ) as key:
            prog_id, _ = winreg.QueryValueEx(key, "ProgId")
            is_default = prog_id == PROG_ID
            print(f"  Current default PDF handler: {prog_id}")
            if is_default:
                print(f"  >> DocView IS the default PDF application")
            else:
                print(f"  >> DocView is NOT the default (to change: Settings > Default Apps > .pdf)")
    except Exception:
        print("  Could not determine default PDF handler.")


def _notify_shell():
    """Tell Windows Explorer to refresh file associations."""
    try:
        from ctypes import windll
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
    except Exception:
        pass


def main():
    if platform.system() != "Windows":
        print(f"This installer is for Windows only. Detected: {platform.system()}")
        print("On Linux, create a .desktop file in ~/.local/share/applications/")
        print("On macOS, bundle as .app with Info.plist CFBundleDocumentTypes")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Register DocView as Windows PDF file handler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install.py              Register for current user
  python install.py --system     Register for all users (admin)
  python install.py --uninstall  Remove all registrations
  python install.py --status     Check registration status
"""
    )
    parser.add_argument("--system", action="store_true",
                        help="Install system-wide (requires admin)")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove DocView file associations")
    parser.add_argument("--status", action="store_true",
                        help="Show current registration status")
    args = parser.parse_args()

    print()
    print("=" * 56)
    print(f"  DocView — File Association Installer")
    print("=" * 56)
    print()

    if args.status:
        show_status()
    elif args.uninstall:
        uninstall()
    elif args.system:
        install_system()
    else:
        install_user()

    print()


if __name__ == "__main__":
    main()
