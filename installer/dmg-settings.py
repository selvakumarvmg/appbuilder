# installer/dmg-settings.py

application = "PremediaApp"
app_path = f"dmg-build/{application}.app"  # <== Must match what you copy earlier

background = "installer-assets/dmg-background.bmp"  # <== Must exist and be BMP/PNG 72DPI

volume_name = "PremediaApp"
icon_size = 128
icon_locations = {
    f"{application}.app": (140, 120),
    "Applications": (380, 120),
}
window_rect = ((100, 100), (520, 280))

codesign_identity = None

symlinks = {
    "Applications": "/Applications"
}
