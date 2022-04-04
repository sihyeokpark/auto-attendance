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
        self.curBtnId = 'all'
        self.HOST = '127.0.0.1'
        self.PORT = 6666
        ## global value init
        self.conFlag = False

        self.friendList = []

    # 친구 목록 생성
    def makeFriendList(self):
        print('making friendList')
        print(self.friendList)
        btnList = []
        mygroupbox = QtWidgets.QGroupBox()
        myform = QtWidgets.QFormLayout()

        qBtn = QPushButton(self)
        qBtn.setGeometry(340, 60 , 111, 28)
        qBtn.setStyleSheet('QPushButton{color: #4C566A;background-color: #D8DEE9;border: 2px solid #4C566A;border-radius: 5px;padding: 5px;margin:3px;}')
        qBtn.setText('all')
        qBtn.show()
        qBtn.clicked.connect(self.friendButtonEvent)
        myform.addRow(qBtn)
        btnList.append(qBtn)

        for i in range(len(self.friendList)):
            qBtn = QPushButton(self)
            qBtn.setGeometry(340, 60 * (i + 1 + 1), 111, 28)
            qBtn.setStyleSheet('QPushButton{color: #4C566A;background-color: #D8DEE9;border: 2px solid #4C566A;border-radius: 5px;padding: 5px;margin:3px;}')
            qBtn.setText(self.friendList[i])
            qBtn.show()
            qBtn.clicked.connect(self.friendButtonEvent)
            myform.addRow(qBtn)
            btnList.append(qBtn)

        mygroupbox.setLayout(myform)
        self.scrollArea.setWidget(mygroupbox)

    def friendButtonEvent(self):
        print("Button Clik")
        btn = self.sender()
        print(btn.text())
        self.curBtnId = btn.text()
        self.lab_chatName.setText('대화 상대 : ' + self.curBtnId)


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

    def payloadParsing(self, payload, msg):
        print('pasloadParsing')
        msgList = msg.split('/')
        if payload == 'FriendList':
            if msgList[1] == 'Receive':
                print('FriendList/Receive')
                print('receive: ' + ''.join(msgList))
                self.friendList = msgList[2].replace(']', '').replace(' ', '').replace('[', '').replace('\'', '').split(',')
                print(self.friendList)
                self.makeFriendList()

    def send(self, msg):
        if self.conFlag:
            print('send message: ' + msg)
            sendMsg = 'Chat/Send/' + msg
            print(sendMsg)
            self.clientSocket.send(sendMsg.encode())
        else:
            QMessageBox.information(self, 'infomation', '서버와의 연결을 확인하세요..')

    # 채팅 엔터치거나 버튼 눌러서 보냈을 때
    def send(self):
        if self.conFlag:
            if not self.le_chat.text():
                QMessageBox.information(self, 'infomation', '빈 메세지입니다.')
                return
            print('send message: ' + self.le_chat.text())
            if len(self.le_chat.text().split('/')) <= 1:
                sendMsg = 'Chat/Send/'+ self.curBtnId + '/' + self.le_chat.text()
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
                    if msgList[2].find('->') != -1:
                        self.parent.tb_chat.append('<span style=\"color:#ff0000;\" >' + msgList[2] + '</span>')
                    else:
                        self.parent.tb_chat.append(msgList[2])

            elif msgList[0] == 'Login':
                if msgList[1] == 'Success':
                    print('login success')
                    self.sigShowMain.emit()
                elif msgList[1] == 'Error':
                    print('login error: ' + msgList[2])
                    # QMessageBox.information(self, 'information', msgList[2])
                    # 에러남. 호출하는 게 main window 가 아니라서 그런가봄
            elif msgList[0] == 'FriendList':
                print('FriendList')
                self.sigPayload.emit(msgList[0], msg)

class LoginWindow(QWidget, loginUi):
    def __init__(self, mainWindow):
        super().__init__()
        self.setupUi(self)
        self.btn_login.clicked.connect(self.login)
        self.btn_signin.clicked.connect(self.signin)
        self.parent = mainWindow
        mainWindow.socketInit()
        mainWindow.connect()

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