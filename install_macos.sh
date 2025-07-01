#!/bin/bash
# macOS Installation Script for PremediaApp

set -e

# Define variables
APP_NAME="PremediaApp"
INSTALL_DIR="/Applications/$APP_NAME.app"
RESOURCES_DIR="$INSTALL_DIR/Contents/Resources"
MACOS_DIR="$INSTALL_DIR/Contents/MacOS"
ICONS_DIR="$RESOURCES_DIR/icons"
DIST_DIR="./dist"
TERMS_FILE="terms.txt"
LICENSE_FILE="license.txt"

echo "Starting PremediaApp installation..."

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Build the application with PyInstaller
echo "Building $APP_NAME with PyInstaller..."
pyinstaller --noconfirm --onefile \
    --add-data "icons:icons" \
    --add-data "terms.txt:." \
    --add-data "license.txt:." \
    --icon icons/premedia.icns \
    --name $APP_NAME main.py

# Create .app bundle structure
echo "Creating .app bundle structure..."
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"
mkdir -p "$ICONS_DIR"

# Move executable and resources
mv "$DIST_DIR/$APP_NAME" "$MACOS_DIR/$APP_NAME"
mv "$DIST_DIR/icons" "$RESOURCES_DIR/"
mv "$DIST_DIR/terms.txt" "$RESOURCES_DIR/"
mv "$DIST_DIR/license.txt" "$RESOURCES_DIR/"

# Create Info.plist with URL protocol registration
cat > "$INSTALL_DIR/Contents/Info.plist" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIconFile</key>
    <string>premedia.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.xai.PremediaApp</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>CFBundleURLTypes</key>
    <array>
        <dict>
            <key>CFBundleURLName</key>
            <string>com.xai.PremediaApp</string>
            <key>CFBundleURLSchemes</key>
            <array>
                <string>premediaapp</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
EOL

# Create log and NAS directories
mkdir -p ~/PremediaApp/Nas
mkdir -p ~/PremediaApp/log
chmod -R u+rw ~/PremediaApp

# Create DMG with a custom background and layout
echo "Creating DMG package..."
hdiutil create -volname "$APP_NAME" -srcfolder "$INSTALL_DIR" -ov -format UDZO "$APP_NAME.dmg"

echo "Installation complete. You can find $APP_NAME.dmg in the current directory."
echo "To install, open $APP_NAME.dmg and drag $APP_NAME.app to the Applications folder."