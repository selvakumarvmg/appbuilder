# installer/dmg-settings.py

application = "PremediaApp"
app_path = "dmg-build/PremediaApp.app"
background = "installer-assets/dmg-background.bmp"

volume_name = "PremediaApp"
icon_size = 128
window_rect = ((200, 200), (480, 360))

dmg_settings = {
    "volume_icon": None,
    "background": background,
    "icon_size": icon_size,
    "window_rect": window_rect,
    "applications_link": True,
    "icon_locations": {
        application: (140, 160),
        "Applications": (340, 160)
    },
}
