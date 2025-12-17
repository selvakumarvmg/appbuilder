# installer/dmg-settings.py

import os

# App name (must match .app name exactly)
application = "PremediaApp.app"

# Volume name shown when DMG is mounted
volume_name = "PremediaApp"

# Background image (relative to repo root)
background = "installer-assets/dmg-background.bmp"

# DMG window size and icon size
icon_size = 128
window_rect = ((200, 200), (480, 360))

# Files included in DMG
files = [
    "dmg-build/PremediaApp.app",
]

# Icon placement inside DMG window
icon_locations = {
    "PremediaApp.app": (140, 160),
    "Applications": (340, 160),
}

# Main dmgbuild configuration
dmg_settings = {
    "volume_name": volume_name,
    "background": background,
    "icon_size": icon_size,
    "window_rect": window_rect,

    # ✅ Creates /Applications shortcut automatically
    "applications_link": True,

    "files": files,
    "icon_locations": icon_locations,

    # UI polish
    "default_view": "icon-view",
    "show_status_bar": False,
    "show_tab_view": False,
    "show_toolbar": False,
    "show_pathbar": False,
    "show_sidebar": False,
    "text_size": 12,
}
