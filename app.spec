# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules
import sysconfig

script_path = "app.py"
project_root = Path(os.getcwd()).resolve()

# === Resource Collection ===
asset_files = [
    (str(f), str(Path("assets") / f.relative_to("assets")))
    for f in Path("assets").rglob("*") if f.is_file()
]
icon_files = [
    (str(f), str(Path("icons") / f.relative_to("icons")))
    for f in Path("icons").rglob("*") if f.is_file()
]
static_files = []
for file in ["TERMS.txt", "LICENSE.txt"]:
    if Path(file).exists():
        static_files.append((file, "."))

data_files = asset_files + icon_files + static_files

# === Include Python dylib only on macOS ===
binaries = []
if sys.platform == "darwin":
    dylib = sysconfig.get_config_var("INSTSONAME")
    if dylib:
        python_dylib_path = Path(sys.executable).parent.parent / "lib" / dylib
        if python_dylib_path.exists():
            binaries.append((str(python_dylib_path), "Frameworks"))
        else:
            print(f"⚠️ WARNING: dylib not found: {python_dylib_path}")

# === Hidden imports ===
hidden_imports = collect_submodules("PySide6")

# === Analysis ===
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

# === Executable ===
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
    target_arch="x86_64",  # Use "arm64" if building on M1/macOS-14
    icon="icons/premedia.icns",
)

# === macOS Bundle ===
app = BUNDLE(
    exe,
    name="PremediaApp.app",
    icon="icons/premedia.icns",
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

# === Final Collection ===
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
