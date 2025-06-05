import sys
import os

from PySide6.QtCore import QTimer, Qt, QTime
from PySide6.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout,
    QSystemTrayIcon, QMenu
)
from PySide6.QtGui import QIcon, QAction


class NotifierApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Notifier")
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)

        self.label = QLabel("Time Notification", self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.hide()

        # Use correct icon format depending on platform
        icon_path = self.get_platform_icon()
        self.tray = QSystemTrayIcon(QIcon(icon_path), self)
        self.tray.setToolTip("Notifier is running in background")
        self.tray.setVisible(True)

        # Tray context menu
        tray_menu = QMenu()
        show_action = QAction("Show Notification Now", self)
        show_action.triggered.connect(self.show_notification)
        tray_menu.addAction(show_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray.setContextMenu(tray_menu)

        # Timer for auto notification every 1 minute
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_notification)
        self.timer.start(1 * 60 * 1000)

        # Show once on startup
        QTimer.singleShot(1000, self.show_notification)

    def get_platform_icon(self):
        """Return appropriate icon path based on OS."""
        if sys.platform.startswith("win"):
            return os.path.join(os.path.dirname(__file__), "pm.ico")
        elif sys.platform.startswith("darwin"):
            return os.path.join(os.path.dirname(__file__), "pm.icns")
        else:
            return os.path.join(os.path.dirname(__file__), "pm.png")

    def show_notification(self):
        current_time = QTime.currentTime().toString("hh:mm:ss AP")
        self.label.setText(f"Current time: {current_time}")
        self.show()

        self.raise_()
        self.activateWindow()
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)

        QTimer.singleShot(5000, self.hide)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def exit_app(self):
        self.tray.setVisible(False)
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray is not available. Exiting.")
        sys.exit(1)

    window = NotifierApp()
    sys.exit(app.exec())
