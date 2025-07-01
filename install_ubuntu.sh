#!/bin/bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip libgtk-3-dev
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
pip3 install pyinstaller
pyinstaller --noconfirm --windowed --icon=icons/premedia.png \
  --add-data "icons:icons" \
  --add-data "terms.txt:." \
  --add-data "license.txt:." \
  --hidden-import=paramiko \
  --hidden-import=tzdata \
  --name PremediaApp app.py
sudo mkdir -p /usr/share/applications
sudo mkdir -p /usr/share/icons/hicolor/scalable/apps
sudo cp dist/icons/premedia.png /usr/share/icons/hicolor/scalable/apps/premedia.png
sudo cp dist/PremediaApp /usr/bin/PremediaApp
sudo cp dist/terms.txt /usr/bin/terms.txt
sudo cp dist/license.txt /usr/bin/license.txt
sudo bash -c "cat > /usr/share/applications/PremediaApp.desktop << EOF
[Desktop Entry]
Name=PremediaApp
Exec=/usr/bin/PremediaApp
Type=Application
Icon=/usr/share/icons/hicolor/scalable/apps/premedia.png
Terminal=false
Categories=Utility;
EOF"
sudo gtk-update-icon-cache /usr/share/icons/hicolor -f || echo "Icon cache update failed"
sudo dpkg-deb --build dist/debian Output/PremediaApp.deb