# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import sysconfig
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# Paths
script_path = "app.py"
project_root = Path(os.getcwd()).resolve()

# Collect all data files
def collect_files(folder_name):
    return [
        (str(f), str(Path(folder_name) / f.relative_to(folder_name)))
        for f in Path(folder_name).rglob("*") if f.is_file()
    ]

asset_files = collect_files("assets")
icon_files = collect_files("icons")
ui_files = collect_files("ui") if Path("ui").exists() else []
static_files = [(f, ".") for f in ["TERMS.txt", "LICENSE.txt"] if Path(f).exists()]

data_files = asset_files + icon_files + ui_files + static_files

from PyInstaller.utils.hooks import collect_data_files
data_files += collect_data_files("PySide6")

# PySide6 hidden imports
hidden_imports = collect_submodules("PySide6")

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
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_file,
)

# macOS bundle
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
    upx=True,
    upx_exclude=[],
    name="PremediaApp",
)
