# installer/dmg-settings.py

# Required settings
application = "PremediaApp"
app_path = f"dmg-build/{application}.app"

# Optional background image
background = "installer-assets/dmg-background.bmp"

# Volume name
volume_name = "PremediaApp"

# Icon location settings
icon_size = 128
icon_locations = {
    f"{application}.app": (140, 120),
    "Applications": (380, 120),
}

# Window size and placement
window_rect = ((100, 100), (520, 280))  # (x, y), (width, height)

# Code signing (disabled here)
codesign_identity = None

# Don't create symlinks
symlinks = {
    "Applications": "/Applications"
}

# Hide hidden files (like .DS_Store)
hide_extensions = True
