# installer/dmg-settings.py

application = "PremediaApp"
app_path = "dmg-build/PremediaApp.app"
background = "installer-assets/dmg-background.bmp"

volume_name = "PremediaApp"
icon_size = 128
window_rect = ((200, 200), (480, 360))

dmg_settings = {
    # Volume name shown on mount
    "volume_name": volume_name,

    # Optional icon for mounted volume
    "volume_icon": None,

    # Background image path
    "background": background,

    # App icon size in the DMG window
    "icon_size": icon_size,

    # Window size and position
    "window_rect": window_rect,

    # Creates shortcut to /Applications in DMG
    "applications_link": True,

    # Icon positions inside DMG window
    "icon_locations": {
        application: (140, 160),
        "Applications": (340, 160)
    },

    # List of actual files to include in the DMG
    "files": [
        (app_path, f"{application}.app")
    ],
}
