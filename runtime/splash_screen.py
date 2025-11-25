from PySide6.QtGui import QPixmap, QColor, QPainter, QImage
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer


class SplashScreen(QWidget):
    def __init__(self, image_path, duration=1200):
        super().__init__()

        self.duration = duration

        # --- Window settings ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # --- Load splash image ---
        self.label = QLabel(self)
        pix = QPixmap(image_path)

        # Scale down to max 40% screen height
        screen = QApplication.primaryScreen().geometry()
        max_h = int(screen.height() * 0.40)
        if pix.height() > max_h:
            pix = pix.scaledToHeight(max_h, Qt.SmoothTransformation)

        self.label.setPixmap(pix)
        self.resize(pix.width(), pix.height())

        # --- Apply glow effect ---
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(40)
        glow.setColor(QColor(255, 255, 255, 120))
        glow.setOffset(0)
        self.label.setGraphicsEffect(glow)

        # Center the splash
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2
        )

        # --- Fade animation ---
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(self.duration)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.finished.connect(self.fade_out)

    def fade_out(self):
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(500)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.InOutQuad)
        fade.finished.connect(self.close)
        fade.start()

    def start(self):
        self.show()
        self.animation.start()
