# installer/dmg-settings.py

application = "PremediaApp"
background = "installer-assets/dmg-background.bmp"

volume_name = "PremediaApp"
icon_size = 128
window_rect = ((200, 200), (480, 360))

files = [
    ("dmg-build/PremediaApp.app", "PremediaApp.app"),
]

dmg_settings = {
    "volume_name": volume_name,
    "volume_icon": None,
    "background": background,
    "icon_size": icon_size,
    "window_rect": window_rect,
    "applications_link": True,
    "icon_locations": {
        application: (140, 160),
        "Applications": (340, 160)
    },
    "files": files,
}
