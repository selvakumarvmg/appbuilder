#!/bin/bash
# Ubuntu Installation Script for PremediaApp

set -e

# Define variables
APP_NAME="PremediaApp"
INSTALL_DIR="/opt/$APP_NAME"
ICONS_DIR="$INSTALL_DIR/icons"
DESKTOP_FILE="/usr/share/applications/premediaapp.desktop"
TERMS_FILE="terms.txt"
LICENSE_FILE="license.txt"
DIST_DIR="./dist"
MIME_TYPE="x-scheme-handler/premediaapp"

echo "Starting $APP_NAME installation..."

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip libegl1-mesa-dev libgl1-mesa-glx

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

# Build the application with PyInstaller
echo "Building $APP_NAME with PyInstaller..."
pyinstaller --noconfirm --onefile \
    --add-data "icons:icons" \
    --add-data "terms.txt:." \
    --add-data "license.txt:." \
    --icon icons/premedia.png \
    --name $APP_NAME main.py

# Create installation directories
sudo mkdir -p "$INSTALL_DIR"
sudo mkdir -p "$ICONS_DIR"
sudo mkdir -p ~/PremediaApp/Nas
sudo mkdir -p ~/PremediaApp/log

# Move files
sudo mv "$DIST_DIR/$APP_NAME" "$INSTALL_DIR/"
sudo mv "$DIST_DIR/icons" "$INSTALL_DIR/"
sudo mv "$DIST_DIR/terms.txt" "$INSTALL_DIR/"
sudo mv "$DIST_DIR/license.txt" "$INSTALL_DIR/"
sudo chmod -R 755 "$INSTALL_DIR"
sudo chmod -R u+rw ~/PremediaApp

# Create desktop file with protocol handler
echo "Creating desktop entry..."
cat > "$DESKTOP_FILE" << EOL
[Desktop Entry]
Name=PremediaApp
Comment=Image Retouching Application
Exec=$INSTALL_DIR/$APP_NAME %u
Type=Application
Terminal=false
Icon=$ICONS_DIR/premedia.png
Categories=Utility;Graphics;
MimeType=$MIME_TYPE;
EOL
sudo chmod 644 "$DESKTOP_FILE"

# Create menu entries for terms and license
cat > "/usr/share/applications/premediaapp-terms.desktop" << EOL
[Desktop Entry]
Name=PremediaApp Terms
Comment=View PremediaApp Terms of Service
Exec=xdg-open $INSTALL_DIR/terms.txt
Type=Application
Terminal=false
Icon=$ICONS_DIR/premedia.png
Categories=Utility;
EOL

cat > "/usr/share/applications/premediaapp-license.desktop" << EOL
[Desktop Entry]
Name=PremediaApp License
Comment=View PremediaApp License
Exec=xdg-open $INSTALL_DIR/license.txt
Type=Application
Terminal=false
Icon=$ICONS_DIR/premedia.png
Categories=Utility;
EOL

sudo chmod 644 /usr/share/applications/premediaapp-*.desktop

# Register custom URL protocol
echo "Registering custom URL protocol..."
sudo xdg-mime default premediaapp.desktop $MIME_TYPE
sudo update-desktop-database

echo "Installation complete. You can find $APP_NAME in your applications menu."