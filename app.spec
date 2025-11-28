# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import sysconfig
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Paths
script_path = "app.py"
project_root = Path(os.getcwd()).resolve()

# Collect all data files recursively
def collect_files(folder_name):
    return [
        (str(f), str(Path(folder_name) / f.relative_to(Path(folder_name))))
        for f in Path(folder_name).rglob("*") if f.is_file()
    ]

asset_files = collect_files("assets") if Path("assets").exists() else []
icon_files = [  # Your existing list... (unchanged)
    ("icons/cache_icon.icns", "icons"),
    # ... all other icons ...
    ("icons/vmg-premedia-logo.png", "icons"),
    ("icons/premedia_splash_screen.png", "icons"),
]
ui_files = [
    ("login.ui", "."),
    ("premediaapp.ui", "."),
    ("icons.qrc", "."),
    ("icons_rc.py", "."),
    ("login.py", "."),
]
static_files = [(f, ".") for f in ["terms.txt", "license.txt"] if Path(f).exists()]

# ✅ NEW: Recursively bundle entire runtime/ (package + subfiles + nested icons)
runtime_files = collect_files("runtime")

# ✅ NEW: Explicitly bundle cache
cache_files = collect_files("cache") if Path("cache").exists() else []

data_files = asset_files + icon_files + ui_files + static_files + runtime_files + cache_files
data_files += collect_data_files("PySide6")
data_files += collect_data_files("PIL")
data_files += collect_data_files("requests")
data_files += collect_data_files("urllib3")
data_files += collect_data_files("paramiko")
data_files += collect_data_files("numpy")
data_files += collect_data_files("psd_tools")

# ✅ PySide6 plugins (unchanged, but added .so for Linux if needed)
from PySide6 import __file__ as pyside6_init
pyside6_dir = Path(pyside6_init).parent
plugins_dir = pyside6_dir / "Qt" / "plugins"
for plugin_subdir in ["platforms", "imageformats"]:
    full_dir = plugins_dir / plugin_subdir
    if full_dir.exists():
        for file in full_dir.glob("*"):
            if file.suffix.lower() in (".dll", ".dylib", ".so"):  # Cross-platform
                rel_path = f"PySide6/Qt/plugins/{plugin_subdir}"
                data_files.append((str(file), rel_path))

hidden_imports = (
    collect_submodules("PySide6") +
    ["paramiko", "tzdata", "PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui", 
     "PySide6.uic", "PIL.Image", "login", "icons_rc", "docopt_ng", "uuid", "httpx", 
     "psd_tools", "rawpy", "tifffile", "imagecodecs", "pid", "pytz", "scp"]
)  # Added your app_runtime.py deps

# macOS dylib (unchanged)
is_macos = sys.platform == "darwin"
binaries = []
if is_macos:
    dylib = sysconfig.get_config_var("INSTSONAME")
    if dylib:
        dylib_path = Path(sys.executable).parent.parent / "lib" / dylib
        if dylib_path.exists():
            binaries.append((str(dylib_path), "Frameworks"))

a = Analysis(
    [script_path],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["runtime-hook.py"],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
icon_file = "icons/premedia.icns" if is_macos else "icons/premedia.ico"
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PremediaApp",
    debug=False,  # True for testing
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # False for GUI
    icon=icon_file,
)
if is_macos:
    app = BUNDLE(
        exe,
        name="PremediaApp.app",
        icon=icon_file,
        bundle_identifier="com.vmgdigital.premediaapp",
        info_plist={
            "CFBundleName": "PremediaApp",
            "CFBundleDisplayName": "PremediaApp",
            "CFBundleExecutable": "PremediaApp",
            "CFBundleIdentifier": "com.vmgdigital.premediaapp",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
        },
    )
coll = COLLECT(
    app if is_macos else exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PremediaApp",
)