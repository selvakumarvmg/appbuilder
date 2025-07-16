import sys
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtGui import QIcon
from login import Ui_Dialog
import icons_rc

# Setup logging
log_dir = Path.home() / ("Library/Application Support/PremediaApp" if sys.platform == "darwin" else "AppData/Roaming/PremediaApp")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(log_dir / "app.log"),
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Log PySide6 plugin paths
try:
    import PySide6
    plugins_path = os.path.join(os.path.dirname(PySide6.__file__), 'plugins')
    logging.debug(f"PySide6 plugins path: {plugins_path}")
    platforms_path = os.path.join(plugins_path, 'platforms')
    imageformats_path = os.path.join(plugins_path, 'imageformats')
    if os.path.exists(platforms_path):
        logging.debug(f"Platforms directory contents: {os.listdir(platforms_path)}")
    else:
        logging.error("Platforms directory not found")
    if os.path.exists(imageformats_path):
        logging.debug(f"Imageformats directory contents: {os.listdir(imageformats_path)}")
    else:
        logging.error("Imageformats directory not found")
except Exception as e:
    logging.error(f"Error checking PySide6 plugins: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PremediaApp Test")
        self.setGeometry(100, 100, 400, 300)

        # Set window icon
        icon_path = resource_path("icons/premedia.icns" if sys.platform == "darwin" else "icons/premedia.ico")
        try:
            icon = QIcon(icon_path)
            if icon.isNull():
                logging.error(f"Failed to load window icon: {icon_path} is null")
            else:
                logging.debug(f"Successfully loaded window icon: {icon_path}")
            self.setWindowIcon(icon)
        except Exception as e:
            logging.error(f"Error loading window icon {icon_path}: {e}")

        # Create layout and button
        layout = QVBoxLayout()
        button = QPushButton("Open Login Dialog")
        try:
            button_icon = QIcon(":/icons/photoshop.png")
            if button_icon.isNull():
                logging.error("Failed to load button icon: :/icons/photoshop.png is null")
            else:
                logging.debug("Successfully loaded button icon: :/icons/photoshop.png")
            button.setIcon(button_icon)
        except Exception as e:
            logging.error(f"Error loading button icon :/icons/photoshop.png: {e}")
        button.clicked.connect(self.show_login_dialog)
        layout.addWidget(button)

        # Set central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def show_login_dialog(self):
        try:
            dialog = QDialog(self)
            ui = Ui_Dialog()
            ui.setupUi(dialog)
            logging.debug("Successfully set up login dialog")
            dialog.exec()
        except Exception as e:
            logging.error(f"Error opening login dialog: {e}")

if __name__ == "__main__":
    # Initialize app
    try:
        app = QApplication(sys.argv)
        logging.debug("QApplication initialized")
    except Exception as e:
        logging.error(f"Failed to initialize QApplication: {e}")
        sys.exit(1)

    # Set app icon
    icon_path = resource_path("icons/premedia.icns" if sys.platform == "darwin" else "icons/premedia.ico")
    try:
        icon = QIcon(icon_path)
        if icon.isNull():
            logging.error(f"Failed to load app icon: {icon_path} is null")
        else:
            logging.debug(f"Successfully loaded app icon: {icon_path}")
        app.setWindowIcon(icon)
    except Exception as e:
        logging.error(f"Error loading app icon {icon_path}: {e}")

    # Test resource icons
    try:
        photoshop_icon = QIcon(":/icons/photoshop.png")
        folder_icon = QIcon(":/icons/folder.png")
        premedia_icon = QIcon(":/icons/premedia.png")
        logo_icon = QIcon(":/icons/vmg-premedia-logo.png")
        if any(icon.isNull() for icon in [photoshop_icon, folder_icon, premedia_icon, logo_icon]):
            logging.error("Failed to load one or more resource icons")
        else:
            logging.debug("Successfully loaded all resource icons")
    except Exception as e:
        logging.error(f"Error loading resource icons: {e}")

    # Show main window
    try:
        window = MainWindow()
        window.show()
        logging.debug("Main window shown")
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"Error showing main window: {e}")
        sys.exit(1)