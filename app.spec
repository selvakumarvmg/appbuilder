# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import sysconfig
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# Paths
script_path = "app.py"
project_root = Path(os.getcwd()).resolve()

# Dynamically locate Python shared library
python_dylib_name = sysconfig.get_config_var("INSTSONAME")  # "libpython3.9.dylib"
python_dylib_path = Path(sys.executable).parent.parent / "lib" / python_dylib_name

# Collect assets
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

static_files = []
for file in ["TERMS.txt", "LICENSE.txt"]:
    if Path(file).exists():
        static_files.append((file, "."))

# Combine data files
data_files = asset_files + icon_files + static_files

# Hidden imports
hidden_imports = collect_submodules("PySide6")

# Analysis block
a = Analysis(
    [script_path],
    pathex=[str(project_root)],
    binaries=[
        (str(python_dylib_path), "Frameworks"),
    ],
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

# PYZ block
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Icon
icon_file = "icons/premedia.icns"

# EXE block
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
    target_arch="x86_64",  # Change to "arm64" for Apple Silicon
    icon=icon_file,
)

# macOS App Bundle
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
        "LSMinimumSystemVersion": "11.0",  # macOS 11+
    },
)

# Final bundle
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
