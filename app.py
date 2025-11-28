from __future__ import annotations

import os
import sys
import json
import time
import traceback
from pathlib import Path

import requests

# PySide6 for errors (fallback)
try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QMessageBox = None

try:
    from tkinter import Tk, Canvas, Frame, Label, BOTH, LEFT, RIGHT, NW, Y, scrolledtext
    from PIL import Image, ImageTk
except Exception:
    Tk = None

# ====================== FULLY HIDDEN & SECURE CONFIG ======================
APP_NAME = "PremediaApp"
BASE_URL = "https://vmg-premedia-22112023.s3.ap-southeast-2.amazonaws.com/application/runtime"

def get_secure_app_dir() -> Path:
    """Returns a hidden, OS-correct, secure folder that users never see"""
    system = sys.platform
    home = Path.home()

    if system == "win32":
        return Path(os.getenv("LOCALAPPDATA", home / "AppData" / "Local")) / APP_NAME
    elif system == "darwin":
        return home / "Library" / "Application Support" / APP_NAME
    else:
        return Path(os.getenv("XDG_CONFIG_HOME", home / ".config")) / APP_NAME.lower()

SECURE_DIR = get_secure_app_dir()
LOCAL_RUNTIME = SECURE_DIR / "runtime"
VERSION_FILE = LOCAL_RUNTIME / "version.json"

DEV_ICONS_SOURCE = Path(r"C:\Users\vmg\Documents\python\appbuilder\icons")

# ====================== SECURE SETUP ======================
def secure_setup():
    for p in (SECURE_DIR, LOCAL_RUNTIME):
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[Secure Setup] Cannot create {p}: {e}")

    if DEV_ICONS_SOURCE.exists():
        icons_target = LOCAL_RUNTIME / "icons"
        icons_target.mkdir(exist_ok=True)
        for src in DEV_ICONS_SOURCE.iterdir():
            if src.suffix.lower() in {".png", ".ico", ".icns", ".jpg", ".jpeg", ".gif"}:
                dest = icons_target / src.name
                try:
                    if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
                        dest.write_bytes(src.read_bytes())
                except:
                    pass

secure_setup()

# ====================== SPLASH IMAGE ======================
def get_splash_image() -> Path | None:
    candidates = [
        LOCAL_RUNTIME / "icons" / "premedia_splash_screen.png",
        LOCAL_RUNTIME / "premedia_splash_screen.png",
        DEV_ICONS_SOURCE / "premedia_splash_screen.png" if DEV_ICONS_SOURCE.exists() else None,
    ]
    for p in candidates:
        if p and p.exists():
            return p
    return None

SPLASH_IMAGE = get_splash_image()

# ====================== SPLASH SCREEN (UNCHANGED) ======================
def show_secure_splash():
    # ... (your full splash code here - unchanged from previous patch) ...
    # [Omitted for brevity; copy from your original or previous response]
    pass  # Placeholder

# ====================== MAIN ======================
def main():
    show_secure_splash()
    
    # ✅ FIXED: Prefer bundled runtime package if frozen (full structure)
    if getattr(sys, 'frozen', False):
        bundled_runtime = Path(sys._MEIPASS) / 'runtime'
        if bundled_runtime.exists():
            # Add bundled path to sys.modules for package import
            sys.path.insert(0, str(bundled_runtime.parent))
            runtime_to_use = bundled_runtime
            print(f"Using bundled runtime: {bundled_runtime}")  # Debug
        else:
            runtime_to_use = LOCAL_RUNTIME
    else:
        runtime_to_use = LOCAL_RUNTIME
    
    # Ensure __init__.py exists (for package)
    init_py = runtime_to_use / "__init__.py"
    if not init_py.exists():
        init_py.touch()
    
    # ✅ FIXED: Import as package (avoids shadowing, resolves sub-imports like from login)
    try:
        sys.path.insert(0, str(runtime_to_use))
        from runtime import app_runtime  # Now imports the module from package
        app_runtime.start_premedia_app()
    except Exception as e:
        error_msg = f"Failed to start: {e}\n{traceback.format_exc()}"
        print(error_msg)
        
        # ✅ FIXED: GUI dialog (no input())
        if PYSIDE_AVAILABLE:
            app = QApplication.instance() or QApplication(sys.argv)
            msg = QMessageBox(QMessageBox.Critical, "Launch Error", 
                              "Failed to launch PremediaApp.")
            msg.setDetailedText(error_msg)
            msg.exec()
        else:
            print(error_msg)
            print("Press Enter to exit...")  # Console fallback
            try:
                input()
            except EOFError:
                pass  # No stdin? Just exit
        
        sys.exit(1)

if __name__ == "__main__":
    main()