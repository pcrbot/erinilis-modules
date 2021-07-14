import os
import re
import sys
import requests
from pathlib import Path
from urllib.parse import parse_qs, quote
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.resize(607, 200)
        MainWindow.setSizeIncrement(QtCore.QSize(0, 0))
        MainWindow.setBaseSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setFamily("黑体")
        font.setPointSize(20)
        font.setStyleStrategy(QtGui.QFont.NoAntialias)
        MainWindow.setFont(font)
        MainWindow.setFocusPolicy(QtCore.Qt.NoFocus)
        MainWindow.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        MainWindow.setLayoutDirection(QtCore.Qt.LeftToRight)
        MainWindow.setStyleSheet("alternate-background-color: rgb(0, 255, 255);")
        MainWindow.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        MainWindow.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.formLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.formLayoutWidget.setGeometry(QtCore.QRect(80, 50, 421, 61))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignCenter)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.server = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.server.setInputMethodHints(QtCore.Qt.ImhFormattedNumbersOnly)
        self.server.setEchoMode(QtWidgets.QLineEdit.Normal)
        self.server.setObjectName("lineEdit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.server)
        self.qq_label = QtWidgets.QLabel(self.formLayoutWidget)
        self.qq_label.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.qq_label)
        self.server_label = QtWidgets.QLabel(self.formLayoutWidget)
        self.server_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.server_label.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.server_label.setFrameShadow(QtWidgets.QFrame.Plain)
        self.server_label.setAlignment(QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.server_label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.server_label)
        self.qq = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.qq.setInputMethodHints(QtCore.Qt.ImhFormattedNumbersOnly)
        self.qq.setEchoMode(QtWidgets.QLineEdit.Normal)
        self.qq.setObjectName("lineEdit_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.qq)
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(20, 10, 561, 31))
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.bindButton = QtWidgets.QPushButton(self.centralwidget)
        self.bindButton.setGeometry(QtCore.QRect(190, 130, 221, 41))
        self.bindButton.setObjectName("pushButton")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "原神卡池绑定"))
        self.server.setText(_translate("MainWindow", "erinilis.cn:7701"))
        self.qq_label.setText(_translate("MainWindow", "绑定的qq号"))
        self.server_label.setText(_translate("MainWindow", "服务器"))
        self.label_3.setText(_translate("MainWindow", "请在游戏内先F3打开抽卡页面后,点击下面的历史记录后在继续"))
        self.bindButton.setText(_translate("MainWindow", "绑定"))


def msg(s):
    msg_box = QMessageBox(QMessageBox.Warning, '提示', s)
    msg_box.exec_()


def handle_bind(url, server, qq):
    if not url:
        msg('url获取失败')
        return
    qs = parse_qs(url)
    if not qs.get('authkey'):
        msg('参数错误. 请重新获取')
        return
    authkey = qs['authkey'][0]
    region = qs['region'][0]
    server = f'http://{server}/genshin/gachalog/bind'
    res = requests.get(f'{server}?region={region}&qq={qq}&authkey={quote(authkey)}', timeout=30).text
    msg(res)


def from_log_file():
    log_file = Path(os.getenv('LOCALAPPDATA') + 'Low') / 'miHoYo' / '原神' / 'output_log.txt'
    if not log_file.exists():
        return msg('找不到本地日志文件, 请确保已经打开过游戏内的卡池历史记录')

    with log_file.open() as f:
        log = f.read()
    url = re.search(r'.+gacha/index.html?(.+)', log)
    if not url:
        return msg('请在游戏内先F3打开抽卡页面后,点击下面的历史记录后在继续')
    return url.group(1)


def bind(server, qq):
    if not qq.isdigit() or int(qq) < 1:
        return msg('只能输入数字啦')

    url = from_log_file()
    if url:
        handle_bind(url, server, qq)
        sys.exit()


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.setupUi(self)
        self.bindButton.clicked.connect(lambda: bind(self.server.text(), self.qq.text()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWindow()
    myWin.show()
    sys.exit(app.exec_())
