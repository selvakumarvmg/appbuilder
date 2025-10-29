# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import sysconfig
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Paths
script_path = "app.py"
project_root = Path(os.getcwd()).resolve()

# Collect all data files
def collect_files(folder_name):
    return [
        (str(f), str(Path(folder_name) / f.relative_to(folder_name)))
        for f in Path(folder_name).rglob("*") if f.is_file()
    ]

asset_files = collect_files("assets") if Path("assets").exists() else []
icon_files = [
    ("icons/cache_icon.icns", "icons"),
    ("icons/cache_icon.ico", "icons"),
    ("icons/cache_icon.png", "icons"),
    ("icons/clear_cache_icon.icns", "icons"),
    ("icons/clear_cache_icon.ico", "icons"),
    ("icons/clear_cache_icon.png", "icons"),
    ("icons/default_icon.icns", "icons"),
    ("icons/default_icon.ico", "icons"),
    ("icons/download_icon.icns", "icons"),
    ("icons/download_icon.ico", "icons"),
    ("icons/download_icon.png", "icons"),
    ("icons/folder.png", "icons"),
    ("icons/login_icon.ico", "icons"),
    ("icons/login_icon.png", "icons"),
    ("icons/logout_icon.icns", "icons"),
    ("icons/logout_icon.ico", "icons"),
    ("icons/logout_icon.png", "icons"),
    ("icons/log_icon.icns", "icons"),
    ("icons/log_icon.ico", "icons"),
    ("icons/log_icon.png", "icons"),
    ("icons/photoshop.png", "icons"),
    ("icons/premedia-logo.bmp", "icons"),
    ("icons/premedia.icns", "icons"),
    ("icons/premedia.ico", "icons"),
    ("icons/premedia.png", "icons"),
    ("icons/quit_icon.ico", "icons"),
    ("icons/report.ico", "icons"),
    ("icons/report.png", "icons"),
    ("icons/upload_icon.icns", "icons"),
    ("icons/upload_icon.ico", "icons"),
    ("icons/upload_icon.png", "icons"),
    ("icons/user_icon.icns", "icons"),
    ("icons/user_icon.ico", "icons"),
    ("icons/user_icon.png", "icons"),
    ("icons/copy_icon.icns", "icons"),
    ("icons/copy_icon.ico", "icons"),
    ("icons/copy_icon.png", "icons"),
    ("icons/retry.icns", "icons"),
    ("icons/retry.ico", "icons"),
    ("icons/retry.png", "icons"),
    ("icons/vmg-premedia-logo.png", "icons"),
    ("icons/version_icon.png", "icons"),
    ("icons/version_icon.ico", "icons"),
    ("icons/version_icon.icns", "icons"),

]
ui_files = [
    ("login.ui", "."),
    ("premediaapp.ui", "."),
    ("icons.qrc", "."),
    ("icons_rc.py", "."),
    ("login.py", "."),
]
static_files = [(f, ".") for f in ["terms.txt", "license.txt"] if Path(f).exists()]

data_files = asset_files + icon_files + ui_files + static_files
data_files += collect_data_files("PySide6")
data_files += collect_data_files("PIL")
data_files += collect_data_files("requests")
data_files += collect_data_files("urllib3")
data_files += collect_data_files("paramiko")
data_files += collect_data_files("numpy")
data_files += collect_data_files("psd_tools")

# ✅ Add PySide6 platform/imageformats plugin .dll files explicitly
from PySide6 import __file__ as pyside6_init
pyside6_dir = Path(pyside6_init).parent
plugins_dir = pyside6_dir / "Qt" / "plugins"

for plugin_subdir in ["platforms", "imageformats"]:
    full_dir = plugins_dir / plugin_subdir
    if full_dir.exists():
        for file in full_dir.glob("*"):
            if file.suffix.lower() == ".dll":
                rel_path = f"PySide6/Qt/plugins/{plugin_subdir}"
                data_files.append((str(file), rel_path))

hidden_imports = (
    collect_submodules("PySide6") +
    ["paramiko", "tzdata", "PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui", "PySide6.uic", "PIL.Image", "login", "icons_rc", "docopt_ng"]
)

# Handle dynamic libpython on macOS
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
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Enable for debugging; switch to False for GUI-only
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
