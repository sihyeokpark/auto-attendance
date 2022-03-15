import sys
import socket

from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import *
from PyQt5 import uic

mainUi = uic.loadUiType("main.ui")[0]
loginUi = uic.loadUiType("login.ui")[0]

class MainWindow(QMainWindow, mainUi):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_send.clicked.connect(self.send)
        self.le_chat.returnPressed.connect(self.send)

        self.HOST = '127.0.0.1'
        self.PORT = 6666
        ## global value init
        self.conFlag = False

    def socketInit(self):
        print('socket init!')
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        if self.conFlag:
            QMessageBox.information(self, "infomation", "이미 서버와 연결이 되었습니다..")
            return

        try:
            self.client_socket.connect((self.HOST, self.PORT))
        except socket.error as msg:
            print("socket Error =: %s\n terminating program" % msg )
            QMessageBox.information(self, "infomation", "서버와의 연결을 확인하세요..")
            return

        print('socket connect success!!')
        self.conFlag = True
        self.recvThread = recvThread(self)
        self.recvThread.start()

    def send(self):
        if self.conFlag:
            print('send message: ' + self.le_chat.text())
            self.client_socket.send(('Chat/Send/' + self.le_chat.text()).encode())
            self.le_chat.setText('')
        else:
            QMessageBox.information(self, 'infomation', '서버와의 연결을 확인하세요..')

    def receive(self):
        msg = self.client_socket.recv(1024).decode()
        msgList = msg.split('/')
        if msgList[0] == 'Chat':
            if msgList[1] == 'Send':
                print('receive message: ' + msgList[2])
                self.tb_chat.append(msgList[2])
        elif msgList[0] == 'Login':
            if msgList[1] == 'Success':
                print('login success: ' + msgList[2])
                mainWindow.show()
                self.close()
            elif msgList[1] == 'Error':
                print('login error: ' + msgList[2])
                QMessageBox.error(self, 'error', msgList[2])

class recvThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        print('recvThread Start')

    def run(self):
        while True:
            self.parent.receive()
        pass

class LoginWindow(QMainWindow, loginUi):
    def __init__(self, mainWindow):
        super().__init__()
        self.setupUi(self)
        self.btn_login.clicked.connect(self.login)
        mainWindow.socketInit()
        mainWindow.connect()

    def login(self):
        if self.conFlag:
            print('login: ' + self.le_id.text())
            self.client_socket.send(('Login/' + self.le_id.text() + '/' + self.le_pw.text()).encode())
        else:
            QMessageBox.information(self, 'infomation', '서버와의 연결을 확인하세요..')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    loginWindow = LoginWindow(mainWindow)
    loginWindow.show()
    app.exec_()