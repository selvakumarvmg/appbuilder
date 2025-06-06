import sys
import os
import platform
import logging
import requests
import urllib3
from PySide6.QtWidgets import (
    QApplication, QDialog, QMessageBox, QProgressDialog, QTextEdit, QSystemTrayIcon,
    QMenu
)
from PySide6.QtGui import QIcon, QTextCursor, QAction
from PySide6.QtCore import Qt, QTimer
from login import Ui_Dialog  # From your .ui file converted to .py
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === Determine OS-specific base directory ===
def get_base_dir():
    system = platform.system()

    if system == "Windows":
        if os.path.exists("D:/"):
            return os.path.join("D:/", "PremediaApp", "Nas")
        else:
            return os.path.join("C:/", "PremediaApp", "Nas")
    elif system == "Darwin":
        return str(Path.home() / "PremediaApp" / "Nas")
    else:  # Linux or other Unix-like
        return str(Path.home() / "PremediaApp" / "Nas")

BASE_TARGET_DIR = get_base_dir()
TARGET_CLIENT_FTP_DIR = os.path.join(BASE_TARGET_DIR, "Client_FTP")
TARGET_SOFTWARE_MEDIA_DIR = os.path.join(BASE_TARGET_DIR, "softwaremedia", "IR_prod")
API_URL = "https://app.vmgpremedia.com/api/ir_production/get/projectList?business=image_retouching"

# === Logger ===
def setup_logger():
    os.makedirs("log", exist_ok=True)
    log_file = os.path.join("log", "app.log")
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
        if len(lines) > 200:
            with open(log_file, 'w') as f:
                f.writelines(lines[-200:])

    logger = logging.getLogger("PremediaApp")
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(file_handler)
    return logger

logger = setup_logger()

# === Folder Creation ===
def create_folders_from_response(response):
    try:
        client_mail = (response.get("client_mail") or "").strip()
        client_name = (response.get("client_name") or client_mail.split("@")[0]).strip()
        project_name = (response.get("project_name") or "").strip()
        job_name = (response.get("job_name") or "").strip()

        ftp_path = os.path.join(BASE_TARGET_DIR, client_name, project_name, job_name)

        os.makedirs(ftp_path, exist_ok=True)

        logger.info(f"Created folders:\n - {ftp_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create folders for {client_name}: {e}")
        return False

# === Log Window ===
class LogWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Log Window")
        self.resize(700, 400)
        self.setWindowIcon(QIcon("pm.png"))
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        from PySide6.QtWidgets import QVBoxLayout
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        self.load_logs()

    def load_logs(self):
        try:
            with open("log/app.log", "r") as f:
                self.text_edit.setPlainText(f.read())
            self.text_edit.moveCursor(QTextCursor.End)
        except Exception as e:
            self.text_edit.setPlainText(f"Failed to load logs: {e}")

# === Login Dialog ===
class LoginDialog(QDialog):
    def __init__(self, tray_icon):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("pm.png"))
        self.setWindowTitle("PremediaApp Login")
        self.tray_icon = tray_icon

        # Disconnect default accepted/rejected behavior to prevent auto close on accept
        self.ui.buttonBox.accepted.disconnect()
        self.ui.buttonBox.rejected.disconnect()

        # Connect custom handlers
        self.ui.buttonBox.accepted.connect(self.handle_login)
        self.ui.buttonBox.rejected.connect(self.reject)

        self.progress = None

    def show_progress(self, message):
        self.progress = QProgressDialog(message, None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setCancelButton(None)
        self.progress.setMinimumDuration(0)
        self.progress.setWindowTitle("Please wait")
        self.progress.show()

    def handle_login(self):
        username = self.ui.usernametxt.toPlainText().strip()
        password = self.ui.passwordtxt.toPlainText().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return

        self.show_progress("Validating credentials...")
        QTimer.singleShot(100, lambda: self.perform_login(username, password))

    def perform_login(self, username, password):
        try:
            token_resp = requests.post(
                "https://app-uat.vmgpremedia.com/oauth/token",
                data={
                    "grant_type": "password",
                    "username": username,
                    "password": password,
                    "client_id": "hZBc4VyhUSQgZobyjdVH7ZPk4WRey2BIjqws_UxF5cM",
                    "client_secret": "crazy-cloud",
                    "scope": "pm_client"
                }, verify=False)
            token_resp.raise_for_status()
            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise Exception("No access token received")

            info_resp = requests.get(
                f"https://app-uat.vmgpremedia.com/api/user/getinfo?emailid={username}",
                headers={"Authorization": f"Bearer {access_token}"}, verify=False)
            info_resp.raise_for_status()
            user_info = info_resp.json()

            user_resp = requests.get(
                f"https://app-uat.vmgpremedia.com/jsonapi/user/user?filter[name]={username}",
                headers={"Authorization": f"Bearer {access_token}"}, verify=False)
            user_resp.raise_for_status()

            project_resp = requests.get(API_URL, verify=False, timeout=60)
            if project_resp.status_code == 200 and isinstance(project_resp.json(), list):
                for item in project_resp.json():
                    create_folders_from_response(item)

            self.progress.close()
            self.tray_icon.show()

            # *** Only hide the login dialog here on success ***
            self.hide()

            QMessageBox.information(self, "Login Success", f"Welcome: {user_info.get('uid', 'Unknown')}")

        except Exception as e:
            logger.error(f"Login error: {e}")
            if self.progress:
                self.progress.close()
            QMessageBox.critical(self, "Login Failed", f"{e}")
            # Keep dialog open for retry (do NOT close/hide it here)

# === Main ===
class PremediaApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.tray_icon = QSystemTrayIcon(QIcon("pm.png"))
        self.tray_icon.setToolTip("PremediaApp")

        self.log_window = LogWindow()
        self.login_dialog = LoginDialog(self.tray_icon)

        tray_menu = QMenu()
        self.logout_action = QAction("Logout")
        self.quit_action = QAction("Quit")
        self.log_action = QAction("View Log Window")

        tray_menu.addAction(self.log_action)
        tray_menu.addAction(self.logout_action)
        tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        self.logout_action.triggered.connect(self.logout)
        self.quit_action.triggered.connect(self.quit)
        self.log_action.triggered.connect(self.show_logs)

        self.tray_icon.show()
        self.login_dialog.show()

    def logout(self):
        self.login_dialog.show()
        QMessageBox.information(None, "Logged Out", "You have been logged out.")

    def quit(self):
        self.tray_icon.hide()
        sys.exit()

    def show_logs(self):
        self.log_window.load_logs()
        self.log_window.show()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == '__main__':
    PremediaApp().run()
