# hello.py
from PySide6.QtWidgets import QApplication, QLabel

app = QApplication([])
label = QLabel("Hello from PyInstaller!")
label.show()
app.exec()
