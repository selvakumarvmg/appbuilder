# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules
import sysconfig

# Paths and settings
script_path = "app.py"
project_root = Path(os.getcwd()).resolve()
icon_file = "icons/premedia.icns"

# Collect asset files
asset_files = [
    (str(f), str(Path("assets") / f.relative_to("assets")))
    for f in Path("assets").rglob("*")
    if f.is_file()
]

# Collect icon files
icon_files = [
    (str(f), str(Path("icons") / f.relative_to("icons")))
    for f in Path("icons").rglob("*")
    if f.is_file()
]

# Add static text files
data_files = []
for file in ["TERMS.txt", "LICENSE.txt"]:
    if Path(file).exists():
        data_files.append((file, "."))

# Collect PySide6 hidden modules
hidden_imports = collect_submodules("PySide6")

# ✅ Dynamically locate and bundle the Python shared library
python_dylib = sysconfig.get_config_var("INSTSONAME")
python_lib_path = Path(sys.executable).parent / python_dylib
python_binary = [(str(python_lib_path), "Frameworks")]

# Analysis section
a = Analysis(
    [script_path],
    pathex=[str(project_root)],
    binaries=python_binary,
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

# Build the archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE file
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PremediaApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid stripping debug symbols
    console=False,
    target_arch="x86_64",  # Target for Intel-based Macs
    icon=icon_file,
)

# macOS .app bundle
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

# Collect everything into the final app bundle
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PremediaApp",
)
