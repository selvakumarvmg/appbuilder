# app.spec
block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icons/premedia.ico', 'icons'),
        ('icons/photoshop.png', 'icons'),
        ('icons/folder.png', 'icons'),
        ('terms.txt', '.'),
        ('license.txt', '.'),
    ],
    hiddenimports=[
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtCore',
        'PySide6.QtSvg',  # Added for potential SVG support
        'PIL.Image',
        'PIL.ImageQt',    # Added for PIL/PySide6 integration
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
    name='PremediaApp',  # Updated to match expected output
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icons/premedia.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='PremediaApp',  # Updated to match expected output
)