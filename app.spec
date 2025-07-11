# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import sysconfig
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# Paths
script_path = "app.py"
project_root = Path(os.getcwd()).resolve()

# -------------------
# Platform-specific binaries
# -------------------
binaries = []

if sys.platform == "darwin":
    python_dylib_name = sysconfig.get_config_var("INSTSONAME")  # usually "libpython3.9.dylib"
    if python_dylib_name:
        python_dylib_path = Path(sys.executable).parent.parent / "lib" / python_dylib_name
        if python_dylib_path.exists():
            binaries.append((str(python_dylib_path), "Frameworks"))
        else:
            print(f"⚠️ Warning: {python_dylib_path} not found.")
    else:
        print("⚠️ INSTSONAME not found in sysconfig.")

# -------------------
# Collect assets
# -------------------
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

# Combine all
data_files = asset_files + icon_files + static_files

# -------------------
# PyInstaller config
# -------------------
hidden_imports = collect_submodules("PySide6")

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

# Use appropriate icon
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

# macOS .app bundle or plain EXE
app_or_exe = (
    BUNDLE(
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
    if sys.platform == "darwin"
    else exe
)

coll = COLLECT(
    app_or_exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PremediaApp",
)
