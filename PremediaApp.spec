# PremediaApp.spec
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Auto-collect all runtime files and plugins for PySide6
pyside6_datas = collect_data_files('PySide6', excludes=[
    'Qt*/Resources',
    'Qt*/Versions/Current/Resources',
])
pyside6_hiddenimports = collect_submodules('PySide6')

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('pm.png', '.'),         # tray icon
        ('TERMS.txt', '.'),
        ('LICENSE.txt', '.'),
        *pyside6_datas,          # ✅ collect all Qt plugins/data
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtNetwork',
        *pyside6_hiddenimports   # ✅ ensure Qt loads its plugins
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PremediaApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='pm.ico' if sys.platform == 'win32' else None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PremediaApp'
)
