import sys

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

        # Setup tray icon with your custom PNG icon
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon("pm.ico"))  # <-- Put your icon file here
        self.tray.setToolTip("Notifier is running in background")
        self.tray.setVisible(True)

        # Tray context menu
        self.tray_menu = QMenu()

        show_action = QAction("Show Notification Now", self)
        show_action.triggered.connect(self.show_notification)
        self.tray_menu.addAction(show_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        self.tray_menu.addAction(exit_action)

        self.tray.setContextMenu(self.tray_menu)

        # Timer for auto notification every 2 minutes
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_notification)
        self.timer.start(1 * 60 * 1000)

        # Show notification once shortly after start
        QTimer.singleShot(1000, self.show_notification)

    def show_notification(self):
        current_time = QTime.currentTime().toString("hh:mm:ss AP")
        self.label.setText(f"Current time: {current_time}")
        self.show()

        # Bring window to front & focus
        self.raise_()
        self.activateWindow()
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)

        # Auto-hide after 5 seconds
        QTimer.singleShot(5000, self.hide)

    def closeEvent(self, event):
        # Hide window instead of closing app
        event.ignore()
        self.hide()

    def exit_app(self):
        self.tray.setVisible(False)  # Hide tray icon
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep app running when window hidden

    window = NotifierApp()
    sys.exit(app.exec())

