#!/bin/bash

APP_NAME="PremediaApp"
VERSION="1.0.0"

BUILD_DIR="dist/debian"
INSTALL_DIR="$BUILD_DIR/usr/share/$APP_NAME"
BIN_DIR="$BUILD_DIR/usr/bin"

mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Copy binary
cp "dist/$APP_NAME" "$INSTALL_DIR/"
echo "#!/bin/bash" > "$BIN_DIR/$APP_NAME"
echo "/usr/share/$APP_NAME/$APP_NAME" >> "$BIN_DIR/$APP_NAME"
chmod +x "$BIN_DIR/$APP_NAME"

# Build .deb
dpkg-deb --build "$BUILD_DIR" "$APP_NAME-$VERSION.deb"
