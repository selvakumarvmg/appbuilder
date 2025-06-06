# Use Ubuntu 22.04 base image for stable glibc version (2.31)
FROM ubuntu:22.04

# Install Python 3.10 and necessary tools
RUN apt-get update && apt-get install -y \
    python3.10 python3.10-venv python3-pip build-essential

# Set working directory inside container
WORKDIR /app

# Copy your app files into container
COPY . /app

# Upgrade pip and install dependencies inside container
RUN python3.10 -m pip install --upgrade pip
RUN python3.10 -m pip install pyinstaller PySide6 requests

# Build your Python app executable with PyInstaller
RUN python3.10 -m PyInstaller --noconfirm --windowed --onefile --icon=pm.png --name=PremediaApp app.py

# Default command to run your app (optional)
CMD ["./dist/PremediaApp"]
