# -------------->  old---> working 
# import os
# import sys
# import time
# import psutil
# import subprocess

# def kill_process_by_name(exe_name):
#     """Terminate any running instance of the old app."""
#     for proc in psutil.process_iter(["name", "pid"]):
#         try:
#             if exe_name.lower() in proc.info["name"].lower():
#                 proc.terminate()
#                 try:
#                     proc.wait(timeout=5)
#                 except psutil.TimeoutExpired:
#                     proc.kill()
#         except Exception:
#             pass


# def main():
#     if len(sys.argv) < 3:
#         print("Usage: updater.exe <new_exe_path> <old_exe_path>")
#         sys.exit(1)

#     new_exe_path = sys.argv[1]   # e.g. C:\Users\Deeran\AppData\Local\Temp\PremediaApp_v1.1.29.exe
#     old_exe_path = sys.argv[2]   # e.g. C:\Users\Deeran\AppData\Local\PremediaApp\PremediaApp.exe
#     exe_name = os.path.basename(old_exe_path)

#     print(f"🔹 Closing old version ({exe_name}) ...")
#     kill_process_by_name(exe_name)

#     # small delay for OS to release file handles
#     time.sleep(1)

#     print(f"🚀 Launching new version from: {new_exe_path}")
#     try:
#         subprocess.Popen([new_exe_path], shell=False)
#         print("✅ Update complete – running the new version (no reinstall).")
#     except Exception as e:
#         print(f"❌ Failed to launch new version: {e}")

#     sys.exit(0)


# if __name__ == "__main__":
#     main()

import os
import sys
import time
import psutil
import subprocess

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel,
    QVBoxLayout, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal


# ==================================================
# Update worker (runs in background)
# ==================================================

class UpdateWorker(QThread):
    status = Signal(str)

    def __init__(self, new_exe, old_exe):
        super().__init__()
        self.new_exe = new_exe
        self.old_exe = old_exe

    def kill_old_process(self):
        exe_name = os.path.basename(self.old_exe)
        self.status.emit(f"Closing {exe_name}...")

        for proc in psutil.process_iter(["name"]):
            try:
                if proc.info["name"] and exe_name.lower() in proc.info["name"].lower():
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        proc.kill()
            except Exception:
                pass

    def run(self):
        try:
            self.kill_old_process()
            time.sleep(1)

            self.status.emit("Launching new version...")
            subprocess.Popen([self.new_exe], shell=False)

            self.status.emit("Update completed")
            time.sleep(1)

        except Exception as e:
            self.status.emit(f"Update failed: {e}")


# ==================================================
# UI
# ==================================================

class UpdaterWindow(QWidget):
    def __init__(self, new_exe, old_exe):
        super().__init__()

        self.setWindowTitle("Updating PremediaApp")
        self.setFixedSize(420, 140)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint)

        self.label = QLabel("Preparing update...")
        self.label.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        self.worker = UpdateWorker(new_exe, old_exe)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.close)

        self.worker.start()

    def update_status(self, text):
        self.label.setText(text)


# ==================================================
# Entry point
# ==================================================

def main():
    if len(sys.argv) < 3:
        sys.exit(1)

    new_exe = sys.argv[1]
    old_exe = sys.argv[2]

    app = QApplication(sys.argv)
    window = UpdaterWindow(new_exe, old_exe)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
