# installer/dmg-settings.py

# Name of your app bundle (must match the .app folder name)
application = "PremediaApp.app"

# Background image (relative to this script or absolute path)
background = "installer-assets/dmg-background.bmp"

# DMG volume name (shown in Finder sidebar and title bar)
volume_name = "PremediaApp"

# Icon size and window layout
icon_size = 128
window_rect = ((200, 200), (600, 400))  # Wider window for better layout

# Files to include in the DMG root (source_path, dest_name_in_dmg)
# dmgbuild will copy PremediaApp.app from dmg-build/ (created in workflow)
files = [application]  # Simple: just the app bundle

# Main settings dictionary
settings = {
    "volume_name": volume_name,
    "volume_icon": None,  # Optional: custom volume icon (.icns)
    "background": background,
    "icon_size": icon_size,
    "window_rect": window_rect,

    # Automatically creates a symlink named "Applications" pointing to /Applications
    "applications_symlink": True,

    # Position the app and the Applications alias
    "icon_locations": {
        application: (150, 200),   # App icon on the left
        "Applications": (450, 200) # Applications shortcut on the right
    },

    # Show a subtle badge on the app icon (optional, looks nice)
    "badge_icon": True,

    # Files/folders to place in the DMG root
    "files": files,

    # Optional: hide file extensions
    "show_file_extensions": False,

    # Default view mode
    "default_view": "icon-view",

    # Arrange icons by name
    "arrange_by": "name",
}

# This is what dmgbuild expects
dmg_settings = settings