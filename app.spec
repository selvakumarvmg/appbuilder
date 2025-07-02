# app.spec
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        ('icons/premedia.ico', 'icons'),
        ('icons/photoshop.png', 'icons'),
        ('icons/folder.png', 'icons'),
        ('terms.txt', '.'),
        ('license.txt', '.'),
    ],
    hiddenimports=[
        *collect_submodules('PySide6'),
        'PIL.Image',
        'PIL.ImageQt',
        'tzdata',
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
    upx=False,  # Disabled due to UPX not being available
    console=False,
    icon='icons/premedia.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='PremediaApp',
)
