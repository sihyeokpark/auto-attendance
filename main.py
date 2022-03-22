import sys
import socket

from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtWidgets

mainUi = uic.loadUiType("main.ui")[0]
loginUi = uic.loadUiType("login.ui")[0]

class MainWindow(QMainWindow, mainUi):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_send.clicked.connect(self.send)
        self.le_chat.returnPressed.connect(self.send)

        self.id = ''

        self.HOST = '127.0.0.1'
        self.PORT = 6666
        ## global value init
        self.conFlag = False

        self.friendList = []

    def makeFriendList(self):
        print('making friendList')
        btnList = []
        mygroupbox = QtWidgets.QGroupBox()
        myform = QtWidgets.QFormLayout()
        for i in range(100):
            qBtn = QPushButton(self)
            qBtn.setGeometry(340, 60 * (i + 1), 111, 28)
            qBtn.setStyleSheet('background-color: rgba(255, 255, 255, 0); color: rgb(255, 255, 255)')
            qBtn.setText(self.friendList[i][1])
            qBtn.show()
            myform.addRow(qBtn)
            btnList.append(qBtn)

        mygroupbox.setLayout(myform)
        self.scrollArea.setWidget(mygroupbox)

    def changeDisplay(self):
        self.login.close()
        self.show()
        ## 친구목록을 서버에 요청
        self.clientSocket.send('FriendList/Get'.encode())
        print('FriendList/Get')

    def idHandle(self, id):
        self.id = id

    def loginHandle(self, login):
        self.login = login


    def socketInit(self):
        print('socket init!')
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        if self.conFlag:
            QMessageBox.information(self, "infomation", "이미 서버와 연결이 되었습니다..")
            return

        try:
            self.clientSocket.connect((self.HOST, self.PORT))
        except socket.error as msg:
            print("socket Error =: %s\n terminating program" % msg )
            QMessageBox.information(self, "infomation", "서버와의 연결을 확인하세요..")
            return

        print('socket connect success!!')
        self.conFlag = True
        self.recvThread = recvThread(self)
        self.recvThread.start()
        self.recvThread.sigShowMain.connect(self.changeDisplay)
        self.recvThread.sigPayload.connect(self.payloadParsing)

    def payloadParsing(self, payload, msgList):
        print('pasloadParsing')
        if payload == 'FriendList':
            if msgList[1] == 'Receive':
                print('FriendList/Receive')
                print('receive: ' + ''.join(msgList))
                self.friendList = list(msgList[2])
                self.makeFriendList()

    def send(self, msg):
        if self.conFlag:
            print('send message: ' + msg)
            sendMsg = 'Chat/Send/' + msg
            print(sendMsg)
            self.clientSocket.send(sendMsg.encode())
        else:
            QMessageBox.information(self, 'infomation', '서버와의 연결을 확인하세요..')

    def send(self):
        if self.conFlag:
            if not self.le_chat.text():
                QMessageBox.information(self, 'infomation', '빈 메세지입니다.')
                return
            print('send message: ' + self.le_chat.text())
            if len(self.le_chat.text().split('/')) <= 1:
                sendMsg = 'Chat/Send/' + self.le_chat.text()
                print(sendMsg)
                self.clientSocket.send(sendMsg.encode())
                self.le_chat.setText('')
        else:
            QMessageBox.information(self, 'infomation', '서버와의 연결을 확인하세요..')


class recvThread(QThread, QObject):
    sigShowMain = pyqtSignal()
    sigPayload = pyqtSignal(str, str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        print('recvThread Start')

    def run(self):
        while True:
            msg = self.parent.clientSocket.recv(1024).decode()
            msgList = msg.split('/')
            if msgList[0] == 'Chat':
                if msgList[1] == 'Send':
                    print('receive message: ' + msgList[2])
                    self.parent.tb_chat.append(msgList[2])
            elif msgList[0] == 'Login':
                if msgList[1] == 'Success':
                    print('login success')
                    self.sigShowMain.emit()
                elif msgList[1] == 'Error':
                    print('login error: ' + msgList[2])
                    QMessageBox.information(self, 'information', msgList[2])
            elif msgList[0] == 'FriendList':
                print('FriendList')
                self.sigPayload.emit(msgList[0], msgList)

class LoginWindow(QWidget, loginUi):
    def __init__(self, mainWindow):
        super().__init__()
        self.setupUi(self)
        self.btn_login.clicked.connect(self.login)
        self.parent = mainWindow
        mainWindow.socketInit()
        mainWindow.connect()

    def login(self):
        if self.parent.conFlag:
            print('login: ' + self.le_id.text())
            self.parent.clientSocket.send(('Login/' + self.le_id.text() + '/' + self.le_pw.text()).encode())
        else:
            QMessageBox.information(self, 'infomation', '서버와의 연결을 확인하세요..')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    loginWindow = LoginWindow(mainWindow)
    mainWindow.loginHandle(loginWindow)
    loginWindow.show()
    app.exec_()