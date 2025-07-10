# installer/dmg-settings.py

application = "PremediaApp"
app_path = f"dmg-build/{application}.app"  # Path to your built .app bundle

# DMG appearance
volume_name = "PremediaApp"  # Shown when DMG is mounted
icon_size = 128
background = "installer-assets/dmg-background.bmp"  # Must be 72 DPI, BMP/PNG format, and exist

# DMG window layout
window_rect = ((100, 100), (520, 280))  # Position (x, y), Size (w, h)

# Icon positions (relative to DMG window)
icon_locations = {
    f"{application}.app": (140, 120),
    "Applications": (380, 120),
}

# Add symlink to /Applications
symlinks = {
    "Applications": "/Applications"
}

# Disable code signing
codesign_identity = None
