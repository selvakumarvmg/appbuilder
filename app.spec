# app.spec
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
is_mac = os.name != "nt"

a = Analysis(
    ['app.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        ('icons/premedia.ico', 'icons'),
        ('icons/photoshop.png', 'icons'),
        ('icons/folder.png', 'icons'),
        ('icons/premedia.icns', 'icons'),
        ('terms.txt', '.'),
        ('license.txt', '.'),
        ('login.ui', '.'),
        ('premediaapp.ui', '.'),
        ('icons.qrc', '.'),
        ('icons_rc.py', '.'),
        ('login.py', '.'),
    ],
    hiddenimports=[
        *collect_submodules('PySide6'),
        'PIL.Image',
        'PIL.ImageQt',
        'tzdata',
        'login',
        'icons_rc',
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
    upx=False,
    console=False,
    icon='icons/premedia.ico' if not is_mac else 'icons/premedia.icns',
)

# Create .app bundle for macOS
app = None
if is_mac:
    app = BUNDLE(
        exe,
        name='PremediaApp.app',
        icon='icons/premedia.icns',
        bundle_identifier='com.vmg.premedia',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleName': 'PremediaApp',
            'CFBundleDisplayName': 'PremediaApp',
            'CFBundleIdentifier': 'com.vmg.premedia',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleIconFile': 'premedia.icns',
        }
    )

# Important fix: pass correct object to COLLECT
coll = COLLECT(
    *( [app] if is_mac else [exe] ),
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='PremediaApp',
)
