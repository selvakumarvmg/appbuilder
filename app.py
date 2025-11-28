# import os
# import sys
# import json
# import time
# from pathlib import Path
# import requests
# from PySide6.QtWidgets import QSplashScreen, QApplication
# from PySide6.QtGui import QPixmap
# from PySide6.QtCore import QTimer, QPropertyAnimation, QByteArray, Qt
# import math
# from PIL import Image, ImageTk, ImageFilter
# from tkinter import Tk, Label

# # -----------------------------------------------------------
# # CONFIG
# # -----------------------------------------------------------
# BASE_URL = (
#     "https://vmg-premedia-22112023.s3.ap-southeast-2.amazonaws.com"
#     "/application/runtime"
# )

# BASE_DIR = Path(__file__).parent.resolve()
# LOCAL_RUNTIME = BASE_DIR / "runtime"
# VERSION_FILE = LOCAL_RUNTIME / "version.json"
# SPLASH_IMAGE = BASE_DIR / "icons" / "premedia_splash_screen.png"


# # -----------------------------------------------------------
# # VERSION HELPERS
# # -----------------------------------------------------------
# def load_local_version():
#     if not VERSION_FILE.exists():
#         return "0.0.0"
#     try:
#         return json.loads(VERSION_FILE.read_text()).get("version", "0.0.0")
#     except:
#         return "0.0.0"


# def load_remote_version():
#     url = f"{BASE_URL}/version.json"
#     try:
#         r = requests.get(url, timeout=10)
#         r.raise_for_status()
#         data = r.json()
#         return data.get("version"), data.get("files", [])
#     except Exception as e:
#         print("[UPDATE ERROR]", e)
#         return None, []


# # -----------------------------------------------------------
# # DOWNLOADER
# # -----------------------------------------------------------
# def download_runtime_file(filename):
#     url = f"{BASE_URL}/{filename}"
#     dest = LOCAL_RUNTIME / filename
#     dest.parent.mkdir(parents=True, exist_ok=True)

#     try:
#         r = requests.get(url, timeout=20)
#         if r.status_code != 200:
#             print(f"[DOWNLOAD ERROR] {filename}: {r.status_code}")
#             return False

#         dest.write_bytes(r.content)
#         print(f"[DOWNLOADED] {filename}")
#         return True

#     except Exception as e:
#         print(f"[DOWNLOAD ERROR] {filename} → {e}")
#         return False


# # -----------------------------------------------------------
# # UPDATER
# # -----------------------------------------------------------
# def run_update():

#     LOCAL_RUNTIME.mkdir(parents=True, exist_ok=True)

#     local = load_local_version()
#     remote, file_list = load_remote_version()

#     print(f"[VERSION] Local={local}, Remote={remote}")

#     if not remote:
#         print("[UPDATER] Cannot reach server. Using local version.")
#         return

#     if local == remote:
#         print("[UPDATER] Already latest.")
#         return

#     print("[UPDATER] Updating…")

#     ok = True
#     for f in file_list:
#         if not download_runtime_file(f):
#             ok = False

#     if not ok:
#         print("[UPDATER] Some files failed. Keeping old version.")
#         return

#     VERSION_FILE.write_text(
#         json.dumps({"version": remote, "files": file_list}, indent=4)
#     )

#     print("[UPDATER] Update complete → Restarting…")

#     os.execl(sys.executable, sys.executable, *sys.argv)


# # -----------------------------------------------------------
# # SPLASH (safe, standalone)
# # -----------------------------------------------------------
# # ---------------------------------------------
# #   TK FADE-IN / FADE-OUT SPLASH SCREEN
# # ---------------------------------------------
# def show_splash(ms: int = 1200):
#     """
#     RESPONSIVE SPLASH SCREEN (FADE-IN + FADE-OUT)
#     -------------------------------------------------
#     ✔ Centers on screen
#     ✔ Auto-scales to max 40% screen height
#     ✔ Keeps aspect ratio
#     ✔ Smooth fade-in / fade-out
#     ✔ Transparent PNG supported
#     ✔ No glow, no zoom, no pulse
#     ✔ Tk only (does NOT affect Qt)
#     """
#     try:
#         if not SPLASH_IMAGE.exists():
#             return

#         import time
#         from tkinter import Tk, Label
#         from PIL import Image, ImageTk

#         root = Tk()
#         root.overrideredirect(True)
#         root.attributes("-topmost", True)
#         root.configure(bg="black")

#         # --- Load image ---
#         img = Image.open(SPLASH_IMAGE).convert("RGBA")
#         iw, ih = img.size

#         sw = root.winfo_screenwidth()
#         sh = root.winfo_screenheight()

#         # --- Responsive scaling (max 40% height) ---
#         max_h = int(sh * 0.40)
#         scale = min(1.0, max_h / ih)
#         nw, nh = int(iw * scale), int(ih * scale)

#         img = img.resize((nw, nh), Image.LANCZOS)

#         # Tk image
#         tk_img = ImageTk.PhotoImage(img)

#         # Create label
#         label = Label(root, image=tk_img, bg="black", bd=0)
#         label.pack()

#         # Center window
#         x = (sw - nw) // 2
#         y = (sh - nh) // 2
#         root.geometry(f"{nw}x{nh}+{x}+{y}")

#         # Make black transparent where supported (Windows)
#         try:
#             root.wm_attributes("-transparentcolor", "black")
#         except:
#             pass

#         # Fade timings
#         fade_steps = 20
#         fade_time = 250  # ms for fade in and fade out
#         fade_delay = fade_time // fade_steps

#         # -------- Fade In --------
#         def fade_in(step=0):
#             if step > fade_steps:
#                 root.after(ms, fade_out)
#                 return
#             alpha = step / fade_steps
#             root.attributes("-alpha", alpha)
#             root.after(fade_delay, lambda: fade_in(step + 1))

#         # -------- Fade Out --------
#         def fade_out(step=0):
#             if step > fade_steps:
#                 root.destroy()
#                 return
#             alpha = 1.0 - (step / fade_steps)
#             root.attributes("-alpha", alpha)
#             root.after(fade_delay, lambda: fade_out(step + 1))

#         root.attributes("-alpha", 0.0)
#         root.after(20, fade_in)
#         root.mainloop()

#     except Exception as e:
#         print("[SPLASH ERROR]", e)

# # -----------------------------------------------------------
# # MAIN ENTRY
# # -----------------------------------------------------------
# if __name__ == "__main__":
#     os.chdir(BASE_DIR)

#     # 1) Update (auto restart)
#     run_update()

#     # 2) Show splash
#     show_splash(2000)

#     # 3) Add runtime folder to import path
#     runtime_path = str(LOCAL_RUNTIME.resolve())
#     sys.path.insert(0, runtime_path)
#     print("[DEBUG] Runtime Path:", runtime_path)

#     # 4) Import your updated runtime application
#     try:
#         import app_runtime
#     except Exception as e:
#         print("\n[IMPORT ERROR] app_runtime failed:", e)
#         raise

#     # 5) Get function
#     try:
#         start_premedia_app = getattr(app_runtime, "start_premedia_app")
#     except:
#         raise RuntimeError("start_premedia_app() not found in app_runtime.py")

#     # 6) Run app (PremediaApp is QApplication inside – do not create QApplication here)
#     start_premedia_app()
# import os
# import sys
# import json
# import time
# from pathlib import Path

# import requests

# # You can keep these PySide6 imports for later if you need them.
# # They are not used in this file directly – PremediaApp lives in app_runtime.py
# from PySide6.QtWidgets import QApplication
# from PySide6.QtGui import QPixmap
# from PySide6.QtCore import Qt

# from PIL import Image, ImageTk

# try:
#     from tkinter import Tk, Label
# except ImportError:
#     Tk = None
#     Label = None

# # -----------------------------------------------------------
# # CONFIG
# # -----------------------------------------------------------
# BASE_URL = (
#     "https://vmg-premedia-22112023.s3.ap-southeast-2.amazonaws.com"
#     "/application/runtime"
# )

# BASE_DIR = Path(__file__).parent.resolve()
# LOCAL_RUNTIME = BASE_DIR / "runtime"
# VERSION_FILE = LOCAL_RUNTIME / "version.json"
# SPLASH_IMAGE = BASE_DIR / "icons" / "premedia_splash_screen.png"


# # -----------------------------------------------------------
# # VERSION HELPERS
# # -----------------------------------------------------------
# def load_local_version() -> str:
#     """Read local runtime/version.json version."""
#     if not VERSION_FILE.exists():
#         return "0.0.0"
#     try:
#         return json.loads(VERSION_FILE.read_text(encoding="utf-8")).get("version", "0.0.0")
#     except Exception:
#         return "0.0.0"


# def load_remote_version():
#     """Get remote version.json from S3."""
#     url = f"{BASE_URL}/version.json"
#     try:
#         r = requests.get(url, timeout=10)
#         r.raise_for_status()
#         data = r.json()
#         return data.get("version"), data.get("files", [])
#     except Exception as e:
#         # Only log to console on hard error – UI will show a generic message
#         print("[UPDATE ERROR]", e)
#         return None, []


# # -----------------------------------------------------------
# # DOWNLOADER
# # -----------------------------------------------------------
# def download_runtime_file(filename: str, status_callback=None) -> bool:
#     """Download a single runtime file and optionally update splash status."""
#     url = f"{BASE_URL}/{filename}"
#     dest = LOCAL_RUNTIME / filename
#     dest.parent.mkdir(parents=True, exist_ok=True)

#     try:
#         if status_callback:
#             status_callback(f"Downloading {filename}…")

#         r = requests.get(url, timeout=20)
#         if r.status_code != 200:
#             if status_callback:
#                 status_callback(f"Download failed: {filename} (HTTP {r.status_code})")
#             print(f"[DOWNLOAD ERROR] {filename}: {r.status_code}")
#             return False

#         dest.write_bytes(r.content)
#         return True

#     except Exception as e:
#         if status_callback:
#             status_callback(f"Download error: {filename}")
#         print(f"[DOWNLOAD ERROR] {filename} → {e}")
#         return False


# # -----------------------------------------------------------
# # UPDATER (UI-AWARE)
# # -----------------------------------------------------------
# def run_update(status_callback=None):
#     """
#     Check & update runtime files.

#     status_callback(msg: str) is used to show messages in the splash UI.
#     It is safe to call this sequentially (no threads).
#     """
#     def ui(msg: str):
#         if status_callback:
#             status_callback(msg)

#     LOCAL_RUNTIME.mkdir(parents=True, exist_ok=True)

#     local = load_local_version()
#     ui("Checking for updates…")

#     remote, file_list = load_remote_version()

#     if not remote:
#         ui("Cannot contact update server. Starting app…")
#         time.sleep(0.8)
#         return

#     if local == remote:
#         ui(f"Up to date (v{local}).")
#         time.sleep(0.8)
#         return

#     ui(f"New version v{remote} found. Updating…")

#     ok = True
#     for f in file_list:
#         if not download_runtime_file(f, status_callback=ui):
#             ok = False
#             break

#     if not ok:
#         ui("Some files failed. Using existing version.")
#         time.sleep(1.0)
#         return

#     ui("Applying update…")
#     VERSION_FILE.write_text(
#         json.dumps({"version": remote, "files": file_list}, indent=4),
#         encoding="utf-8",
#     )

#     ui("Update complete. Restarting app…")
#     time.sleep(1.0)

#     # Hard restart with new runtime
#     os.execl(sys.executable, sys.executable, *sys.argv)


# # -----------------------------------------------------------
# # TK FADE-IN / FADE-OUT SPLASH WITH STATUS
# # -----------------------------------------------------------
# def show_splash_with_update():
#     """
#     RESPONSIVE SPLASH SCREEN with STATUS + FADE
#     -------------------------------------------------
#     ✔ Centers on screen
#     ✔ Auto-scales to max 40% screen height
#     ✔ Keeps aspect ratio
#     ✔ Fade-in, hold, fade-out
#     ✔ Status text: checking / downloading / starting
#     ✔ All work (update) happens while splash is visible
#     ✔ No interference with Qt (QApplication starts AFTER this)
#     """
#     if Tk is None or Label is None:
#         # Tk not available: just run update without splash
#         run_update(status_callback=None)
#         return

#     if not SPLASH_IMAGE.exists():
#         # No image → just run update
#         run_update(status_callback=None)
#         return

#     try:
#         root = Tk()
#         root.overrideredirect(True)
#         root.attributes("-topmost", True)
#         root.configure(bg="black")

#         # --- Load & scale image ---
#         img = Image.open(SPLASH_IMAGE).convert("RGBA")
#         iw, ih = img.size

#         sw = root.winfo_screenwidth()
#         sh = root.winfo_screenheight()

#         max_h = int(sh * 0.40)   # 40% of screen height
#         scale = min(1.0, max_h / float(ih))
#         nw, nh = int(iw * scale), int(ih * scale)
#         img = img.resize((nw, nh), Image.LANCZOS)

#         tk_img = ImageTk.PhotoImage(img)

#         # --- Layout: Image + Status label ---
#         img_label = Label(root, image=tk_img, bg="black")
#         img_label.pack(fill="both", expand=False, padx=0, pady=(0, 8))

#         status_label = Label(
#             root,
#             text="Checking updates...",
#             bg="black",
#             fg="white",
#             font=("Segoe UI", 12),
#             anchor="center"
#         )
#         status_label.pack(fill="x", expand=False, padx=10, pady=(0, 8))

#         # ---- Compute total splash height ----
#         label_height = 32     # fixed height for status text
#         padding = 16          # extra bottom padding
#         total_height = nh + label_height + padding

#         x = (sw - nw) // 2
#         y = (sh - total_height) // 2
#         root.geometry(f"{nw}x{total_height}+{x}+{y}")

#         # Make black transparent where supported (Windows)
#         try:
#             root.wm_attributes("-transparentcolor", "black")
#         except Exception:
#             pass

#         # Helper to update status text + repaint
#         def set_status(msg: str):
#             status_label.config(text=msg)
#             root.update_idletasks()
#             root.update()

#         # -------- Fade In --------
#         fade_steps = 20
#         fade_time_ms = 250
#         step_delay = fade_time_ms / fade_steps / 1000.0

#         root.attributes("-alpha", 0.0)
#         for step in range(fade_steps + 1):
#             alpha = step / float(fade_steps)
#             root.attributes("-alpha", alpha)
#             root.update_idletasks()
#             root.update()
#             time.sleep(step_delay)

#         # -------- Run update while splash is visible --------
#         run_update(status_callback=set_status)

#         # After update (if no restart happened):
#         set_status("Starting application…")
#         time.sleep(0.8)

#         # -------- Fade Out --------
#         for step in range(fade_steps + 1):
#             alpha = 1.0 - (step / float(fade_steps))
#             root.attributes("-alpha", alpha)
#             root.update_idletasks()
#             root.update()
#             time.sleep(step_delay)

#         root.destroy()

#     except Exception as e:
#         print("[SPLASH ERROR]", e)
#         # On any error, just run update without UI
#         run_update(status_callback=None)


# # -----------------------------------------------------------
# # MAIN ENTRY
# # -----------------------------------------------------------
# if __name__ == "__main__":
#     os.chdir(BASE_DIR)

#     # 1) Show splash + run update WITH status messages
#     show_splash_with_update()

#     # 2) Add runtime folder to import path
#     runtime_path = str(LOCAL_RUNTIME.resolve())
#     if runtime_path not in sys.path:
#         sys.path.insert(0, runtime_path)
#     print("[DEBUG] Runtime Path:", runtime_path)

#     # 3) Import your updated runtime application
#     try:
#         import app_runtime
#     except Exception as e:
#         print("\n[IMPORT ERROR] app_runtime failed:", e)
#         raise

#     # 4) Find start_premedia_app
#     try:
#         start_premedia_app = getattr(app_runtime, "start_premedia_app")
#     except AttributeError:
#         raise RuntimeError("start_premedia_app() not found in app_runtime.py")

#     # 5) Run app (PremediaApp is QApplication inside – do NOT create QApplication here)
#     start_premedia_app()


# launcher.py  (replace your current app2.py / app.py with this)
#!/usr/bin/env python3
"""
PremediaApp launcher (cross-platform, production-ready)
- Shows a responsive Tk splash with status (fade-in/out)
- Runs updater from S3 while splash is visible (status_label updates)
- Downloads runtime files to a user-writable runtime folder per-platform
- Dynamically resolves icons from runtime icons folder, falling back to bundled icons
- Safe permission fallbacks if APP_DATA_DIR isn't writable
"""
from __future__ import annotations

import os
import sys
import json
import time
import traceback
from pathlib import Path

import requests

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
        # Hidden by Windows Explorer by default
        return Path(os.getenv("LOCALAPPDATA", home / "AppData" / "Local")) / APP_NAME
    elif system == "darwin":
        # Hidden in ~/Library (invisible in Finder unless Show Hidden)
        return home / "Library" / "Application Support" / APP_NAME
    else:
        # Linux: hidden dot folder in ~/.config (standard & invisible)
        return Path(os.getenv("XDG_CONFIG_HOME", home / ".config")) / APP_NAME.lower()

# Secure hidden runtime folder — never visible to users
SECURE_DIR = get_secure_app_dir()
LOCAL_RUNTIME = SECURE_DIR / "runtime"
VERSION_FILE = LOCAL_RUNTIME / "version.json"

# Optional: dev icons (only used on your dev machine)
DEV_ICONS_SOURCE = Path(r"C:\Users\vmg\Documents\python\appbuilder\icons")  # Only you see this

# ====================== SECURE SETUP ======================
def secure_setup():
    for p in (SECURE_DIR, LOCAL_RUNTIME):
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[Secure Setup] Cannot create {p}: {e}")

    # Copy your dev icons only if source exists (safe fallback)
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

# ====================== SPLASH IMAGE (FROM HIDDEN FOLDER) ======================
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

# ====================== FINAL SECURE + HIDDEN SPLASH ======================
def show_secure_splash():
    if not (Tk and SPLASH_IMAGE and SPLASH_IMAGE.exists()):
        print("Running silently (no splash)...")
        return

    root = Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg="#1e1e1e")
    root.resizable(False, False)

    # Load & scale image
    try:
        img = Image.open(SPLASH_IMAGE).convert("RGBA")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        scale = min(0.70, sh * 0.55 / img.height)
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
    except:
        root.destroy()
        return

    container = Frame(root, bg="#1e1e1e")
    container.pack(fill=BOTH, expand=True)

    canvas = Canvas(container, width=new_w, height=new_h, bg="#1e1e1e", highlightthickness=0)
    canvas.pack(side=LEFT, fill=Y)
    canvas.create_image(0, 0, image=photo, anchor=NW)

    panel = Frame(container, bg="#2d2d2d", padx=28, pady=28)
    panel.pack(side=RIGHT, fill=BOTH, expand=True)

    # Best cross-platform fonts
    def font(size, weight=""):
        return ("Segoe UI" if sys.platform == "win32" else "Helvetica", size, weight)

    Label(panel, text="PremediaApp", font=font(19, "bold"), fg="#00bfff", bg="#2d2d2d")\
        .pack(anchor="w", pady=(0, 6))
    ver_label = Label(panel, text="Checking...", font=font(11), fg="#b0b0b0", bg="#2d2d2d")
    ver_label.pack(anchor="w", pady=(0, 12))
    status_label = Label(panel, text="Initializing...", font=font(13, "bold"), fg="#ffffff", bg="#2d2d2d")
    status_label.pack(anchor="w", pady=(0, 18))

    log_frame = Frame(panel, bg="#252525")
    log_frame.pack(fill=BOTH, expand=True)

    log = scrolledtext.ScrolledText(
        log_frame, width=42, height=18,
        bg="#252525", fg="#e0e0e0",
        font=("Consolas", 10) if sys.platform == "win32" else ("Menlo", 10),
        state="disabled", wrap="word", relief="flat", bd=0,
        padx=16, pady=16, insertbackground="#00bfff"
    )
    log.pack(fill=BOTH, expand=True)

    root.update_idletasks()
    root.geometry(f"+{(sw - root.winfo_width())//2}+{(sh - root.winfo_height())//2}")

    # Fade in
    root.attributes("-alpha", 0.0)
    for a in range(0, 101, 10):
        root.attributes("-alpha", a/100)
        root.update()
        time.sleep(0.012)

    line = 0
    def log_msg(text: str, kind: str = "info"):
        nonlocal line
        line += 1
        icons = {"success": "Success", "failed": "Failed", "downloading": "Downloading", "info": "Info"}
        colors = {"success": "#00ff9d", "failed": "#ff6b6b", "downloading": "#ffd93d", "info": "#00bfff"}
        icon = icons.get(kind, "Info")
        color = colors.get(kind, "#e0e0e0")
        log.config(state="normal")
        log.insert("end", f"{icon} {text}\n")
        tag = f"l{line}"
        log.tag_add(tag, f"{line}.0", f"{line}.end")
        log.tag_config(tag, foreground=color)
        log.see("end")
        log.config(state="disabled")
        root.update()

    def set_status(t): status_label.config(text=t); root.update()
    def set_version(t): ver_label.config(text=t); root.update()

    # Update logic
    set_status("Checking for updates...")
    log_msg("Launcher started", "info")

    local_ver = "0.0.0"
    if VERSION_FILE.exists():
        try:
            local_ver = json.loads(VERSION_FILE.read_text("utf-8", errors="ignore")).get("version", "0.0.0")
        except:
            pass

    try:
        r = requests.get(f"{BASE_URL}/version.json", timeout=15)
        r.raise_for_status()
        data = r.json()
        remote_ver = data.get("version")
        files = data.get("files", [])
    except:
        remote_ver = None
        files = []

    if not remote_ver:
        set_version(f"v{local_ver} • Offline")
        set_status("No internet")
        log_msg("Server unreachable", "failed")
        time.sleep(2)
    else:
        set_version(f"v{local_ver} → v{remote_ver}")
        if local_ver >= remote_ver:
            set_status("Up to date")
            log_msg("No update needed", "success")
            time.sleep(1.2)
        else:
            set_status("Updating...")
            log_msg(f"Downloading {len(files)} files", "info")
            ok = 0
            for f in files:
                name = f.split("/")[-1]
                log_msg(name, "downloading")
                dest = LOCAL_RUNTIME / f
                try:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    r = requests.get(f"{BASE_URL}/{f}", timeout=60)
                    r.raise_for_status()
                    dest.write_bytes(r.content)
                    log_msg(name, "success")
                    ok += 1
                except:
                    log_msg(f"{name} failed", "failed")
                time.sleep(0.04)

            if ok == len(files):
                try:
                    VERSION_FILE.write_text(json.dumps({"version": remote_ver, "files": files}, indent=4))
                except:
                    pass
                set_status("Update complete")
                log_msg("Restarting...", "success")
                time.sleep(1.2)
                root.destroy()
                os.execl(sys.executable, sys.executable, *sys.argv)

    set_status("Launching PremediaApp...")
    time.sleep(1.0)

    for a in range(100, -10, -10):
        root.attributes("-alpha", a/100)
        root.update()
        time.sleep(0.02)

    root.destroy()

# ====================== MAIN ======================
def main():
    show_secure_splash()
    sys.path.insert(0, str(LOCAL_RUNTIME.resolve()))
    try:
        import app_runtime
        app_runtime.start_premedia_app()
    except Exception as e:
        print(f"Failed to start: {e}")
        traceback.print_exc()
        input("Press Enter...")

if __name__ == "__main__":
    main()