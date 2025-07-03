import sys
from pathlib import Path
import os

# Define the main script and project root
script_path = "app.py"
project_root = Path(os.getcwd()).resolve()

# Collect all asset and icon files recursively
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
data_files = [
    ("TERMS.txt", "."),
    ("LICENSE.txt", ".")
]

a = Analysis(
    [script_path],
    pathex=[str(project_root)],
    binaries=[],
    datas=asset_files + icon_files + data_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=a.cipher)

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
    icon="icons/premedia.ico" if sys.platform == "win32" else None,
)

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
