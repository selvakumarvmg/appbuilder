# dmg-settings.py

# Required
application = "PremediaApp.app"
output_filename = "PremediaApp.dmg"
volume_name = "PremediaApp Installer"

# Icon background image (must be 640x480 or similar ratio)
background = "installer-assets/dmg-background.bmp"  # Put this image in the same folder or adjust the path

icon_locations = {
    "PremediaApp.app": (140, 120),
    "Applications": (500, 120)
}

# Optional settings
show_status_bar = False
show_tab_view = False
show_toolbar = False
sidebar_width = 180

# Set this to `True` for transparent background support on macOS 10.13+
use_hdiutil = True
