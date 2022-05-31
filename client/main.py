import sys
import socket

import registerFace

from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtWidgets

mainUi = uic.loadUiType("main.ui")[0]
loginUi = uic.loadUiType("login.ui")[0]

class MainWindow(QMainWindow, mainUi):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("exon main")

        self.btn_send.clicked.connect(self.send)
        self.le_chat.returnPressed.connect(self.send)

        self.logLevel = 1

        self.id = ''
        self.curBtnId = 'all'
        self.HOST = '192.168.35.82'
        self.PORT = 6666
        ## global value init
        self.conFlag = False

        self.friendList = []

    def log(self, msg, level=2):
        if level < self.logLevel:
            print('[Log] ' + msg)

    # 친구 목록 생성
    def makeFriendList(self):
        self.log('making friendList')
        self.log(self.friendList)
        btnList = []
        mygroupbox = QtWidgets.QGroupBox()
        myform = QtWidgets.QFormLayout()

        qBtn = QPushButton(self)
        qBtn.setGeometry(340, 60, 111, 48)
        qBtn.setStyleSheet("QPushButton { border: none; background-color: #2f3545; border-radius: 10px; color: #ffffff; } QPushButton:hover { background-color: #49526b; color: #ffffff; }")
        qBtn.setText('all')
        qBtn.show()
        qBtn.clicked.connect(self.friendButtonEvent)
        myform.addRow(qBtn)
        btnList.append(qBtn)

        for i in range(len(self.friendList)):
            qBtn = QPushButton(self)
            qBtn.setGeometry(340, 60 * (i + 1 + 1), 111, 48)
            qBtn.setStyleSheet("QPushButton { border: none; background-color: #2f3545; border-radius: 10px; color: #ffffff; } QPushButton:hover { background-color: #49526b; color: #ffffff; }")
            qBtn.setText(self.friendList[i])
            qBtn.show()
            qBtn.clicked.connect(self.friendButtonEvent)
            myform.addRow(qBtn)
            btnList.append(qBtn)

        mygroupbox.setLayout(myform)
        self.scrollArea.setWidget(mygroupbox)

    def friendButtonEvent(self):
        self.log("Button Clik")
        btn = self.sender()
        self.log(btn.text())
        self.curBtnId = btn.text()
        self.lab_chatName.setText('대화 상대 : ' + self.curBtnId)


    # 로그인 창 꺼지게
    def changeDisplay(self):
        self.login.close()
        self.show()

    def idHandle(self, id):
        self.id = id

    def loginHandle(self, login):
        self.login = login

    def showError(self, msg):
        QMessageBox.information(self, 'information', msg)


    def socketInit(self):
        self.log('socket init!', 0)
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connecttoServer(self):
        if self.conFlag:
            QMessageBox.information(self, "infomation", "이미 서버와 연결이 되었습니다..")
            return

        try:
            self.clientSocket.connect((self.HOST, self.PORT))
        except socket.error as msg:
            self.log("socket Error =: %s\n terminating program" % msg, 0)
            QMessageBox.information(self, "infomation", "서버와의 연결을 확인하세요..")
            return

        self.log('socket connect success!!', 0)
        self.conFlag = True
        self.recvThread = recvThread(self)
        self.recvThread.start()
        self.recvThread.sigShowMain.connect(self.changeDisplay)
        self.recvThread.sigPayload.connect(self.payloadParsing)

    def payloadParsing(self, payload, msg):
        self.log('pasloadParsing', 1)
        msgList = msg.split('/')
        if payload == 'FriendList':
            if msgList[1] == 'Receive':
                self.log('FriendList/Receive', 1)
                self.log('receive: ' + ''.join(msgList), 1)
                self.friendList = msgList[2].replace(']', '').replace(' ', '').replace('[', '').replace('\'', '').split(',')
                self.log(self.friendList, 2)
                self.makeFriendList()

    def send(self, msg):
        if self.conFlag:
            self.log('send message: ' + msg, 0)
            sendMsg = 'Chat/Send/' + msg
            self.log(sendMsg)
            self.clientSocket.send(sendMsg.encode())
        else:
            QMessageBox.information(self, 'infomation', '서버와의 연결을 확인하세요..')

    # 채팅 엔터치거나 버튼 눌러서 보냈을 때
    def send(self):
        if self.conFlag:
            if not self.le_chat.text():
                QMessageBox.information(self, 'infomation', '빈 메세지입니다.')
                return
            self.log('send message: ' + self.le_chat.text(), 0)
            if len(self.le_chat.text().split('/')) <= 1:
                sendMsg = 'Chat/Send/' + self.curBtnId + '/' + self.le_chat.text()
                self.log(sendMsg)
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

        self.logLevel = 1

        self.log('recvThread Start', 0)

    def log(self, msg, level=2):
        if level < self.logLevel:
            print('[Log] ' + msg)

    def run(self):
        while True:
            msg = self.parent.clientSocket.recv(1024).decode()
            msgList = msg.split('/')
            if msgList[0] == 'Chat':
                if msgList[1] == 'Send':
                    self.log('receive message: ' + msgList[2])
                    if msgList[2].find('->') != -1:
                        self.parent.tb_chat.append('<span style=\"color:#ff0000;\" >' + msgList[2] + '</span>')
                    else:
                        self.parent.tb_chat.append('<span style=\"color:#000000;\" >' + msgList[2] + '</span>')

            elif msgList[0] == 'Login':
                if msgList[1] == 'Success':
                    self.log('login success', 0)
                    self.sigShowMain.emit()
                elif msgList[1] == 'Error':
                    self.log('login error: ' + msgList[2], 0)
                    # self.parent.showError(msgList[2])
                    # 에러남. 호출하는 게 main window 가 아니라서 그런가봄
                    if msgList[2] == '이미 접속 중인 아이디입니다.':
                        return
            elif msgList[0] == 'FriendList':
                self.log('FriendList')
                self.sigPayload.emit(msgList[0], msg)

class LoginWindow(QWidget, loginUi):
    def __init__(self, mainWindow):
        super().__init__()
        self.setupUi(self)
        self.btn_login.clicked.connect(self.login)
        self.btn_signin.clicked.connect(self.signin)
        self.btn_registerFace.clicked.connect(self.registerFaceCall)
        self.setWindowTitle("exon login")
        self.parent = mainWindow
        mainWindow.socketInit()
        mainWindow.connecttoServer()

    def registerFaceCall(self):
        self.hide()
        self.registerWindow = registerFace.registerFaceWindow()
        self.registerWindow.exec()
        self.show()
        print("------------------------------keep alive")

    def login(self):
        if self.parent.conFlag:
            print('login: ' + self.le_id.text())
            self.parent.clientSocket.send(('Login/' + self.le_id.text() + '/' + self.le_pw.text()).encode())
        else:
            QMessageBox.information(self, 'infomation', '서버와의 연결을 확인하세요..')

    def signin(self):
        if self.parent.conFlag:
            print('signin: ' + self.le_id.text())
            self.parent.clientSocket.send(('Signin/' + self.le_id.text() + '/' + self.le_pw.text()).encode())
        else:
            QMessageBox.information(self, 'infomation', '서버와의 연결을 확인하세요..')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    loginWindow = LoginWindow(mainWindow)
    mainWindow.loginHandle(loginWindow)
    loginWindow.show()
    app.exec_()