# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import sysconfig
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

script_path = "app.py"
project_root = Path(os.getcwd()).resolve()

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

data_files = asset_files + icon_files + static_files
hidden_imports = collect_submodules("PySide6")

# Binaries (macOS only)
binaries = []
if sys.platform == "darwin":
    dylib_name = sysconfig.get_config_var("INSTSONAME")  # "libpython3.9.dylib"
    if dylib_name:
        dylib_path = Path(sys.executable).parent.parent / "lib" / dylib_name
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
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Icon file (platform-specific)
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
    target_arch="x86_64",  # Use arm64 if needed
    icon=icon_file,
)

# macOS .app bundle
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

coll = COLLECT(
    exe,  # ✅ not `app`, PyInstaller handles `.app`
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PremediaApp",
)
