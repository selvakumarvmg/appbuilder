# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

script_path = "app.py"
project_root = Path(os.getcwd()).resolve()

# Collect assets and icons
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

# Static data files
data_files = []
for file in ["TERMS.txt", "LICENSE.txt"]:
    if Path(file).exists():
        data_files.append((file, "."))

hidden_imports = collect_submodules("PySide6")

a = Analysis(
    [script_path],
    pathex=[str(project_root)],
    binaries=[],
    datas=asset_files + icon_files + data_files,
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

# Use .icns for macOS
icon_file = "icons/premedia.icns"

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
    },
)

# Critical fix: use `exe` here, not `app`
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
