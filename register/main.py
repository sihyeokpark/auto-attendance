import sys
import socket

from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtWidgets

mainUi = uic.loadUiType("main.ui")[0]

class MainWindow(QMainWindow, mainUi):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.btn_picture.clicked.connect(self.picture)
        self.btn_register.clicked.connect(self.register)

    def picture(self):
        pass

    def register(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()