import socket
import threading
import sqlite3
import time
import utils
import sys

from PyQt5.QtCore import QThread

from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui

serverUi = uic.loadUiType("server.ui")[0]

class ServerWindow(QWidget, serverUi):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("exon server")

        self.clientList = []
        self.HOST = '192.168.35.82'
        self.PORT = 6666

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.HOST, self.PORT))
        self.serverSocket.listen()

        idRefreshThread = userIDRefresh(self)
        idRefreshThread.start()

        print('server start')

        self.makeThread()

    def makeThread(self):
        while True:
            print('wait')

            clientSocket, addr = self.serverSocket.accept()
            print('client accpet addr = ', addr)
            t = mainThread(self, clientSocket, addr)
            t.start()

        serverSocket.close()

# 설정된 시간 마다 접속된 Client의 user id를 refresh하는 Thread
class userIDRefresh(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        while True:
            time.sleep(1)
            try:
                idList = []
                for i in self.parent.clientList:
                    idList.append(i[1])

                for client in self.parent.clientList:
                    client[0].send(('FriendList/Receive/' + str(idList)).encode())

            except:
                print("userIDRefresh Thread Error!!")


class mainThread(QThread):
    def __init__(self, parent, clientSocket, addr):
        super().__init__(parent)
        self.clientSocket = clientSocket
        self.addr = addr
        self.parent = parent

    def run(self):
        clientID = ''
        print('Connected by :', self.addr[0], ':', self.addr[1])
        try:
            conn = sqlite3.connect("user.db")
            cur = conn.cursor()

            while True:
                data = self.clientSocket.recv(1024)
                # msg = utils.removeBreakText(data)
                msg = data.decode()
                msgList = msg.split('/')
                if msgList[0] == 'Chat':
                    if msgList[1] == 'Send':
                        print('receive message: ' + msgList[3])
                        if msgList[2] == 'all':
                            for client in self.parent.clientList:
                                client[0].send(('Chat/Send/' + clientID + ': ' + msgList[3]).encode())
                        else:
                            for client in self.parent.clientList:
                                if msgList[2] == client[1]:
                                    client[0].send(
                                        ('Chat/Send/' + clientID + ' -> ' + msgList[2] + ': ' + msgList[3]).encode())
                            self.clientSocket.send(
                                ('Chat/Send/' + clientID + ' -> ' + msgList[2] + ': ' + msgList[3]).encode())
                elif msgList[0] == 'Login':
                    if msgList[1] != '' and msgList[2] != '':
                        query = "SELECT * FROM user WHERE id='%s'" % msgList[1]
                        cur.execute(query)
                        fetch = cur.fetchone()
                        userId = ''
                        pwd = ''
                        print(fetch)
                        if not fetch:
                            self.clientSocket.send('Login/Error/아이디가 존재하지 않습니다.'.encode())
                        else:
                            userId, pwd = fetch
                        isIdAlready = False
                        if msgList[1] == userId:
                            if msgList[2] == pwd:
                                for client in self.parent.clientList:
                                    if client[1] == msgList[1]:
                                        self.clientSocket.send('Login/Error/이미 접속 중인 아이디입니다.'.encode())
                                        isIdAlready = True
                                if not isIdAlready:
                                    print('add friendlist: ' + msgList[1])
                                    self.parent.clientList.append((self.clientSocket, msgList[1]))
                                    print(self.parent.clientList)
                                    self.clientSocket.send('Login/Success'.encode())
                                    clientID = userId
                            else:
                                self.clientSocket.send('Login/Error/비밀번호가 맞지 않습니다.'.encode())
                elif msgList[0] == 'FriendList':
                    if msgList[1] == 'Get':
                        print('friendList get: ' + str(self.parent.clientList))
                        idList = []
                        for i in self.parent.clientList:
                            idList.append(i[1])
                        self.clientSocket.send(('FriendList/Receive/' + str(idList)).encode())
                elif msgList[0] == 'Signin':
                    if msgList[1] != '' and msgList[2] != '':
                        query = 'INSERT INTO user VALUES (\'' + msgList[1] + '\',\'' + msgList[2] + '\')'
                        cur.execute(query)
                        conn.commit()
                        print('signin: ' + msgList[1])

        except ConnectionResetError as e:
            print('Disconnected by ' + self.addr[0], ':', self.addr[1])
            self.clientSocket.close()
            # List에서 빠진 Client의 ID를 제거...
            if (self.clientSocket, clientID) in self.parent.clientList:
                self.parent.clientList.remove((self.clientSocket, clientID))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = ServerWindow()
    mainWindow.show()
    app.exec_()