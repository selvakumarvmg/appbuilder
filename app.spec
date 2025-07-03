# app.spec - Updated for PremediaApp cross-platform build

# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

app_name = "PremediaApp"
script_path = "app.py"

# Cross-platform icon selection
if sys.platform.startswith("win"):
    icon_file = "icons/premedia.ico"
elif sys.platform.startswith("darwin"):
    icon_file = "icons/premedia.icns"
else:
    icon_file = "icons/premedia.png"

# Hidden imports for PySide6 plugins (required for GUI to render correctly)
hiddenimports = collect_submodules("PySide6")

a = Analysis(
    [script_path],
    pathex=[str(Path(".").resolve())],
    binaries=[],
    datas=[
        ("assets/*", "assets"),
        ("icons/*", "icons"),
        ("TERMS.txt", "."),
        ("LICENSE.txt", ".")
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name
)
