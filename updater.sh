# #!/bin/bash
set -euo pipefail

NEW_DMG="$1"

if [ ! -f "$NEW_DMG" ]; then
    echo "❌ DMG not found: $NEW_DMG"
    exit 1
fi

echo "▶️ Mounting the update DMG..."
hdiutil attach "$NEW_DMG" -nobrowse -mountpoint "/Volumes/PremediaApp" > /dev/null

VOLUME="/Volumes/PremediaApp"

if [ ! -d "$VOLUME" ]; then
    echo "❌ Failed to mount DMG"
    exit 1
fi

echo "✅ Opening the mounted volume..."
open "$VOLUME"

# Clear, friendly instructions for unsigned app
osascript <<EOF
display dialog "Update ready!\n\nPlease drag PremediaApp.app from this window to the Applications folder shortcut (→).\n\nImportant: On first launch of the new version:\n• It may say the app is damaged — this is normal for unsigned apps.\n• Go to System Settings > Privacy & Security\n• Scroll down and click \"Open Anyway\" next to PremediaApp." buttons {"OK"} default button "OK" with title "PremediaApp Update" with icon note
EOF

echo "✅ Update instructions shown."
exit 0


# #!/bin/bash
# set -euo pipefail

# NEW_DMG="$1"
# APP_NAME="PremediaApp.app"
# INSTALL_DIR="/Applications"
# MOUNT_POINT="/Volumes/PremediaApp"

# if [ ! -f "$NEW_DMG" ]; then
#   echo "❌ DMG not found: $NEW_DMG"
#   exit 1
# fi

# echo "▶️ Mounting DMG..."
# hdiutil attach "$NEW_DMG" -nobrowse -mountpoint "$MOUNT_POINT" > /dev/null

# if [ ! -d "$MOUNT_POINT/$APP_NAME" ]; then
#   echo "❌ App not found inside DMG: $MOUNT_POINT/$APP_NAME"
#   hdiutil detach "$MOUNT_POINT" > /dev/null || true
#   exit 1
# fi

# echo "🧹 Removing old app..."
# rm -rf "$INSTALL_DIR/$APP_NAME"

# echo "📦 Installing new app..."
# cp -R "$MOUNT_POINT/$APP_NAME" "$INSTALL_DIR/"

# echo "🔓 Removing quarantine..."
# xattr -dr com.apple.quarantine "$INSTALL_DIR/$APP_NAME" || true

# echo "⏏️ Unmounting DMG..."
# hdiutil detach "$MOUNT_POINT" > /dev/null

# echo "🚀 Launching updated app..."
# open "$INSTALL_DIR/$APP_NAME"


