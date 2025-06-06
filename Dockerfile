# Use Ubuntu 22.04 base image for stable glibc version (2.31)
FROM ubuntu:22.04

# Install Python 3.10 and necessary tools including dpkg-dev
RUN apt-get update && apt-get install -y \
    python3.10 python3.10-venv python3-pip build-essential dpkg-dev

# Set working directory inside container
WORKDIR /app

# Copy your app files into container
COPY . /app

# Upgrade pip and install dependencies inside container
RUN python3.10 -m pip install --upgrade pip
RUN python3.10 -m pip install pyinstaller PySide6 requests

# Build your Python app executable with PyInstaller
RUN python3.10 -m PyInstaller --noconfirm --windowed --onefile --icon=pm.png --name=PremediaApp app.py

# Prepare Debian package structure and control file
RUN mkdir -p package-root/DEBIAN package-root/usr/local/bin && \
    cp dist/PremediaApp package-root/usr/local/bin/ && \
    chmod 755 package-root/usr/local/bin/PremediaApp && \
    echo "Package: premediaapp" > package-root/DEBIAN/control && \
    echo "Version: 1.0.0" >> package-root/DEBIAN/control && \
    echo "Section: utils" >> package-root/DEBIAN/control && \
    echo "Priority: optional" >> package-root/DEBIAN/control && \
    echo "Architecture: amd64" >> package-root/DEBIAN/control && \
    echo "Depends: libc6 (>= 2.31)" >> package-root/DEBIAN/control && \
    echo "Maintainer: Your Name <your.email@example.com>" >> package-root/DEBIAN/control && \
    echo "Description: PremediaApp - Your Python desktop app packaged as .deb" >> package-root/DEBIAN/control && \
    echo " A Python desktop application packaged using PyInstaller." >> package-root/DEBIAN/control

# Build the .deb package
RUN dpkg-deb --build package-root

# Optional: Move the .deb file to a known location
RUN mv package-root.deb /app/PremediaApp_1.0.0_amd64.deb

# Default command to run your app (optional)
CMD ["./dist/PremediaApp"]
