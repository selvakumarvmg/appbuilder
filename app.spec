# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import sysconfig
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

script_path = "app.py"
project_root = Path(os.getcwd()).resolve()

# 🔍 Shared library for macOS
binaries = []
if sys.platform == "darwin":
    dylib_name = sysconfig.get_config_var("INSTSONAME")
    if dylib_name:
        dylib_path = Path(sys.executable).parent.parent / "lib" / dylib_name
        if dylib_path.exists():
            binaries.append((str(dylib_path), "Frameworks"))

# 📦 Data files
asset_files = [
    (str(f), str(Path("assets") / f.relative_to("assets")))
    for f in Path("assets").rglob("*")
    if f.is_file()
]
icon_files = [
    (str(f), str(Path("icons") / f.relative_to("icons")))
    for f in Path("icons").rglob("*")
    if f.is_file()
]
text_files = [(f, ".") for f in ["TERMS.txt", "LICENSE.txt"] if Path(f).exists()]
data_files = asset_files + icon_files + text_files

# 🕵️ Hidden imports
hidden_imports = collect_submodules("PySide6")

# 🧪 Analysis
a = Analysis(
    [script_path],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 🎯 Platform icon
icon_file = "icons/premedia.icns" if sys.platform == "darwin" else "icons/premedia.ico"

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

# 🍎 macOS .app bundle (optional)
if sys.platform == "darwin":
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

# 📦 Collect the EXE (always pass `exe`, not the BUNDLE)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PremediaApp",
)
