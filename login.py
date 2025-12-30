# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QDialog,
    QDialogButtonBox, QGroupBox, QLabel, QLineEdit,
    QSizePolicy, QWidget)
import icons_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(764, 616)
        icon = QIcon()
        icon.addFile(u":/newPrefix/premedia.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setAutoFillBackground(False)
        Dialog.setStyleSheet(u"/* =====================================================\n"
"GLOBAL BASE\n"
"===================================================== */\n"
"QWidget {\n"
"    background-color: #f2f2f2;\n"
"    font-family: \"Segoe UI\", sans-serif;\n"
"    font-size: 14px;\n"
"    color: #1f1f1f;\n"
"}\n"
"\n"
"/* =====================================================\n"
"MAIN CONTAINER (NO CARD, NO FLOAT)\n"
"===================================================== */\n"
"QGroupBox {\n"
"    background-color: #ffffff;\n"
"    border: 1px solid #dcdcdc; \n"
"    border-radius: 22px;\n"
"    padding: 10px;\n"
"box-shadow: 5px 5px 10px #888888;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    subcontrol-position: top left;\n"
"    padding: 6px;\n"
"    margin: 10px 20px 15px 20px;\n"
"	\n"
"    font-size: 13px;\n"
"    font-weight: 600;\n"
"    color: #005fb8;\n"
"}\n"
"\n"
"/* =====================================================\n"
"LABELS\n"
"===================================================== */\n"
"Q"
                        "Label {\n"
"    background: transparent;\n"
"    font-size: 13px;\n"
"    color: #2b2b2b;\n"
"}\n"
"\n"
"QLabel#label {\n"
"    font-size: 18px;\n"
"    font-weight: 600;\n"
"    color: #1f1f1f;\n"
"    qproperty-alignment: AlignCenter;\n"
"    margin-bottom: 12px;\n"
"}\n"
"\n"
"/* =====================================================\n"
"INPUT FIELDS (REAL DESKTOP STYLE)\n"
"===================================================== */\n"
"QLineEdit {\n"
"    background-color: #ffffff;\n"
"    border: 1px solid #bdbdbd;\n"
"    border-radius: 4px;\n"
"    padding: 6px 8px;\n"
"    font-size: 13px;\n"
"    color: #1f1f1f;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #005fb8;\n"
"    background-color: #ffffff;\n"
"}\n"
"\n"
"QLineEdit::placeholder {\n"
"    color: #7a7a7a;\n"
"}\n"
"\n"
"/* Password field */\n"
"QLineEdit#passwordtxt {\n"
"    letter-spacing: 0.5px;\n"
"}\n"
"\n"
"/* =====================================================\n"
"CHECKBOX / RADIO (NATIVE-LIKE)\n"
"=========================="
                        "=========================== */\n"
"QCheckBox,\n"
"QRadioButton {\n"
"    spacing: 6px;\n"
"    font-size: 13px;\n"
"    color: #1f1f1f;\n"
"}\n"
"\n"
"QCheckBox::indicator,\n"
"QRadioButton::indicator {\n"
"    width: 14px;\n"
"    height: 14px;\n"
"}\n"
"\n"
"QCheckBox::indicator {\n"
"    border: 1px solid #7a7a7a;\n"
"    background: #ffffff;\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"    background-color: #005fb8;\n"
"    border-color: #005fb8;\n"
"}\n"
"\n"
"/* =====================================================\n"
"BUTTONS (REAL TOOL BUTTONS)\n"
"===================================================== */\n"
"QPushButton {\n"
"    background-color: #005fb8;\n"
"    color: #ffffff;\n"
"    border: 1px solid #005fb8;\n"
"    padding: 6px 16px;\n"
"    font-size: 13px;\n"
"    font-weight: 600;\n"
"    border-radius: 4px;\n"
"    min-width: 90px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #0a6fd6;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #004a92;\n"
"}\n"
"\n"
""
                        "/* Secondary / Cancel */\n"
"QPushButton#btnCancel {\n"
"    background-color: #ffffff;\n"
"    color: #005fb8;\n"
"    border: 1px solid #bdbdbd;\n"
"}\n"
"\n"
"QPushButton#btnCancel:hover {\n"
"    background-color: #f2f2f2;\n"
"}\n"
"\n"
"/* =====================================================\n"
"DIALOG BUTTON BOX\n"
"===================================================== */\n"
"QDialogButtonBox QPushButton {\n"
"    min-width: 90px;\n"
"}\n"
"")
        self.groupBox = QGroupBox(Dialog)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(60, 130, 631, 431))
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        font.setBold(True)
        self.groupBox.setFont(font)
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(100, 170, 161, 31))
        self.label_3.setFont(font)
        self.usernametxt = QLineEdit(self.groupBox)
        self.usernametxt.setObjectName(u"usernametxt")
        self.usernametxt.setGeometry(QRect(100, 90, 441, 61))
        font1 = QFont()
        font1.setFamilies([u"Segoe UI"])
        self.usernametxt.setFont(font1)
        self.passwordtxt = QLineEdit(self.groupBox)
        self.passwordtxt.setObjectName(u"passwordtxt")
        self.passwordtxt.setGeometry(QRect(100, 200, 441, 61))
        self.passwordtxt.setFont(font1)
        self.passwordtxt.setEchoMode(QLineEdit.Password)
        self.rememberme = QCheckBox(self.groupBox)
        self.rememberme.setObjectName(u"rememberme")
        self.rememberme.setEnabled(True)
        self.rememberme.setGeometry(QRect(100, 270, 181, 31))
        self.rememberme.setFont(font1)
        self.rememberme.setStyleSheet(u"background : #fff")
        self.rememberme.setCheckable(True)
        self.rememberme.setChecked(True)
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(100, 60, 171, 30))
        self.label_2.setFont(font)
        self.buttonBox = QDialogButtonBox(self.groupBox)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(280, 320, 261, 81))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.showPasswordRadioButton = QCheckBox(self.groupBox)
        self.showPasswordRadioButton.setObjectName(u"showPasswordRadioButton")
        self.showPasswordRadioButton.setGeometry(QRect(420, 270, 121, 27))
        self.showPasswordRadioButton.setStyleSheet(u"background : #fff")
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(240, 10, 261, 121))
        self.label.setPixmap(QPixmap(u":/icons/icons/vmg-premedia-logo.png"))
        self.label.setScaledContents(True)

        self.retranslateUi(Dialog)
        self.buttonBox.rejected.connect(Dialog.reject)
        self.buttonBox.accepted.connect(Dialog.accept)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Premedia App Login", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", u"LOGIN", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"Enter Password Here", None))
        self.usernametxt.setPlaceholderText(QCoreApplication.translate("Dialog", u"USER EMAIL ID", None))
        self.passwordtxt.setPlaceholderText(QCoreApplication.translate("Dialog", u"USER PASSWORD", None))
        self.rememberme.setText(QCoreApplication.translate("Dialog", u"Remember Password", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Enter User Name Here", None))
        self.showPasswordRadioButton.setText(QCoreApplication.translate("Dialog", u"Show Password", None))
        self.label.setText("")
    # retranslateUi

