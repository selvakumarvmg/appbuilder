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
        Dialog.resize(764, 669)
        icon = QIcon()
        icon.addFile(u":/newPrefix/premedia.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        Dialog.setWindowIcon(icon)
        Dialog.setStyleSheet(u"/* ===============================\n"
"\ud83c\udf10 Base Form Style (Clean/Neutral)\n"
"================================== */\n"
"QDialog, QWidget {\n"
"    background-color: #f4f6f8;  /* light neutral background */\n"
"    font-family: \"Segoe UI\", \"Helvetica Neue\", sans-serif;\n"
"    font-size: 14px;\n"
"    color: #333333;\n"
"}\n"
"\n"
"/* ===============================\n"
"\ud83d\uddbc\ufe0f QLabel Styling\n"
"================================== */\n"
"QLabel {\n"
"    background-color: transparent;\n"
"    font-size: 13px;\n"
"    color: #2e2e2e;\n"
"}\n"
"\n"
"QLabel#label_2,\n"
"QLabel#label_3 {\n"
"    background-color: #e0e0e0;\n"
"    padding: 6px 10px;\n"
"    border-radius: 0px 5px 0px 5px;\n"
"    font-weight: 500;\n"
"    color: #1a1a1a;\n"
"}\n"
"\n"
"QLabel#label {\n"
"    qproperty-alignment: AlignCenter;\n"
"    padding: 10px;\n"
"}\n"
"\n"
"/* ===============================\n"
"\ud83d\udce6 QGroupBox Styling\n"
"================================== */\n"
"QGroupBox {\n"
"    background-c"
                        "olor: #ffffff;\n"
"    border: 1px solid #d1d1d1;\n"
"    border-radius: 10px;\n"
"    padding: 20px;\n"
"    margin-top: 10px;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"QGroupBox::title {\n"
"    subcontrol-origin: content;\n"
"    subcontrol-position: top left;\n"
"    margin-top: -12px;\n"
"    padding: 4px 10px;\n"
"    font-size: 15px;\n"
"    color: #0078d7;\n"
"}\n"
"\n"
"/* ===============================\n"
"\ud83d\udd24 QLineEdit (Inputs)\n"
"================================== */\n"
"QLineEdit {\n"
"    background-color: #ffffff;\n"
"    border: 1px solid #bfc5ca;\n"
"    border-radius: 6px;\n"
"    padding: 8px 12px;\n"
"    font-size: 13px;\n"
"    color: #333;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #0078d7;\n"
"    background-color: #f0faff;\n"
"}\n"
"\n"
"/* ===============================\n"
"\u2705 QCheckBox with Clean Label Background\n"
"================================== */\n"
"QCheckBox {\n"
"    spacing: 6px;\n"
"    font-size: 13px;\n"
"    color: #1a1a1a;\n"
"    padd"
                        "ing: 6px 8px;\n"
"    border-radius: 6px;\n"
"    background-color: #eeeeee;\n"
"}\n"
"\n"
"QCheckBox::indicator {\n"
"    width: 16px;\n"
"    height: 16px;\n"
"    border-radius: 3px;\n"
"    border: 1px solid #999;\n"
"    background-color: #ffffff;\n"
"}\n"
"\n"
"QCheckBox::indicator:checked {\n"
"    background-color: #0078d7;\n"
"    image: none;\n"
"}\n"
"\n"
"QCheckBox::indicator:hover {\n"
"    border: 1px solid #3399ff;\n"
"}\n"
"\n"
"/* ===============================\n"
"\ud83d\udd18 QRadioButton Styling\n"
"================================== */\n"
"QRadioButton {\n"
"    spacing: 6px;\n"
"    font-size: 13px;\n"
"    color: #2e2e2e;\n"
"    padding: 6px 8px;\n"
"}\n"
"\n"
"QRadioButton::indicator {\n"
"    width: 16px;\n"
"    height: 16px;\n"
"    border-radius: 8px;\n"
"    border: 2px solid #0078d7;\n"
"    background-color: white;\n"
"}\n"
"\n"
"QRadioButton::indicator:checked {\n"
"    background-color: #0078d7;\n"
"}\n"
"\n"
"QRadioButton::indicator:unchecked {\n"
"    background-color: whit"
                        "e;\n"
"    border: 2px solid #bbb;\n"
"}\n"
"\n"
"/* ===============================\n"
"\ud83e\udde9 QPushButton Styling (Flat & Modern)\n"
"================================== */\n"
"QPushButton {\n"
"    background-color: #0078d7;\n"
"    color: white;\n"
"    padding: 8px 16px;\n"
"    border-radius: 5px;\n"
"    font-weight: bold;\n"
"    min-width: 90px;\n"
"    min-height: 30px;\n"
"    border: none;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #005a9e;\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #004578;\n"
"}\n"
"\n"
"/* ===============================\n"
"\ud83d\udcac QDialogButtonBox Buttons\n"
"================================== */\n"
"QDialogButtonBox QPushButton {\n"
"    background-color: #0078d7;\n"
"    color: white;\n"
"    padding: 8px 16px;\n"
"    border-radius: 5px;\n"
"    font-weight: bold;\n"
"    border: none;\n"
"    min-width: 90px;\n"
"    min-height: 30px;\n"
"}\n"
"\n"
"QDialogButtonBox QPushButton:hover {\n"
"    background-color: #005a9e;\n"
"}"
                        "\n"
"\n"
"QDialogButtonBox QPushButton:pressed {\n"
"    background-color: #004578;\n"
"}\n"
"")
        self.groupBox = QGroupBox(Dialog)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(60, 130, 631, 461))
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        font.setBold(True)
        self.groupBox.setFont(font)
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(90, 200, 161, 31))
        self.label_3.setFont(font)
        self.usernametxt = QLineEdit(self.groupBox)
        self.usernametxt.setObjectName(u"usernametxt")
        self.usernametxt.setGeometry(QRect(80, 120, 441, 61))
        font1 = QFont()
        font1.setFamilies([u"Segoe UI"])
        self.usernametxt.setFont(font1)
        self.passwordtxt = QLineEdit(self.groupBox)
        self.passwordtxt.setObjectName(u"passwordtxt")
        self.passwordtxt.setGeometry(QRect(80, 230, 441, 61))
        self.passwordtxt.setFont(font1)
        self.passwordtxt.setEchoMode(QLineEdit.Password)
        self.rememberme = QCheckBox(self.groupBox)
        self.rememberme.setObjectName(u"rememberme")
        self.rememberme.setEnabled(True)
        self.rememberme.setGeometry(QRect(80, 310, 181, 31))
        self.rememberme.setFont(font1)
        self.rememberme.setCheckable(True)
        self.rememberme.setChecked(True)
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(90, 90, 171, 30))
        self.label_2.setFont(font)
        self.buttonBox = QDialogButtonBox(self.groupBox)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(350, 370, 251, 61))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(240, 10, 271, 121))
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
        self.label.setText("")
    # retranslateUi

