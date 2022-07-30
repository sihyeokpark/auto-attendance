import socket
import sqlite3
import time
import datetime
import utils
import sys
import schedule

from PyQt5.QtCore import QThread

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic, QtGui

serverUi = uic.loadUiType('server.ui')[0]
scheduleUi = uic.loadUiType('schedule.ui')[0]

class ScheduleWindow(QDialog, scheduleUi):
    setSchedule = pyqtSignal(int, list, bool)

    def __init__(self, parent, modi=False, chatList=None, itemList = None):
        super().__init__()
        self.parent = parent
        self.modi = modi
        self.chatList = chatList
        self.itemList = itemList
        self.setupUi(self)
        self.setWindowTitle('exon server')

        if self.modi: ## 수정모드
            self.teDate.setText(itemList[1])
            self.teTime.setText(itemList[2])
            self.teWho.setText(itemList[3])
            self.teNotice.setText(itemList[4])
        else:
            pass
        self.btnSave.clicked.connect(self.saveSchedule)

        for data in self.chatList:
            self.cbWho.addItem(data[1])

        #self.cbWho.currentIndexChanged.connect(self.onCbWhoChanged)
        self.cbWho.activated[str].connect(self.onCbWhoChanged)

    def saveSchedule(self):
        dateValue = self.teDate.toPlainText()
        timeValue = self.teTime.toPlainText()
        whoValue = self.teWho.toPlainText()
        noticeValue = self.teNotice.toPlainText()

        rowPosition = self.parent.twSchedule.rowCount()
        if self.modi:
            rowPosition = int(self.itemList[0])
        else:
            self.parent.twSchedule.insertRow(rowPosition)

        itemList = [str(rowPosition), dateValue, timeValue, whoValue, noticeValue]
        self.setSchedule.emit(rowPosition, itemList, self.modi)


        # monday, tuesday, wednesday, thursday, friday, saturday, sunday
        if dateValue == '월요일': schedule.every().monday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue))
        elif dateValue == '화요일': schedule.every().tuesday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue))
        elif dateValue == '수요일': schedule.every().wednesday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue))
        elif dateValue == '목요일': schedule.every().thursday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue))
        elif dateValue == '금요일': schedule.every().friday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue))
        elif dateValue == '토요일': schedule.every().saturday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue))
        elif dateValue == '일요일': schedule.every().sunday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue))


        self.close()


    def onCbWhoChanged(self, value):
        print(value)
        self.teWho.setText(self.teWho.toPlainText() + value + ', ')


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

        self.btnRegister.clicked.connect(self.registerSchedule)
        self.btnModify.clicked.connect(self.modifySchedule)
        self.btnDelete.clicked.connect(self.deleteSchedule)

        idRefreshThread = userIDRefresh(self)
        idRefreshThread.start()

        print('server start')

        makingThread = makeThread(self)
        makingThread.start()

        showingConnectedUsers = showConnectedUsers(self)
        showingConnectedUsers.userClear.connect(self.clearUser)
        showingConnectedUsers.userAdd.connect(self.addUser)
        showingConnectedUsers.start()

        runSchedule = RunSchedule(self)
        runSchedule.start()

    def executeSchedule(self, data):
        whoList = data[0].split(',')[:-1]
        for client in self.clientList:
            if client[1] in whoList:
                print('Schedule/Send/' + data[1])
                client[0].send(('Schedule/Send/' + data[1]).encode())


    def deleteSchedule(self):
        x = self.twSchedule.selectedIndexes()
        self.twSchedule.removeRow(x[0].row())

    def registerSchedule(self):
        scheduleWindow = ScheduleWindow(self, False, self.clientList)
        scheduleWindow.setSchedule.connect(self.setItem)
        scheduleWindow.exec_()

    def modifySchedule(self):
        x = self.twSchedule.selectedIndexes()
        itemList = [self.twSchedule.item(x[0].row(), 0).text(), self.twSchedule.item(x[0].row(), 1).text(), self.twSchedule.item(x[0].row(), 2).text(), self.twSchedule.item(x[0].row(), 3).text(), self.twSchedule.item(x[0].row(), 4).text()]
        scheduleWindow = ScheduleWindow(self, True, self.clientList, itemList)
        scheduleWindow.setSchedule.connect(self.setItem)
        scheduleWindow.exec_()

    def addLog(self, text):
        self.tb_log.append(text)

    @pyqtSlot(str)
    def addUser(self, text):
        self.tb_user.append(text)

    @pyqtSlot()
    def clearUser(self):
        self.tb_user.clear()

    @pyqtSlot(int, list, bool)
    def setItem(self, row, itemList, isModify):
        if isModify:
            for i in range(5):
                 self.twSchedule.item(row, i).setText(itemList[i])
        else:
            for i in range(5):
                 self.twSchedule.setItem(row, i, QTableWidgetItem(itemList[i]))

class RunSchedule(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

# 서버의 "접속 유저" 보여주는 클래스
class showConnectedUsers(QThread, QObject):
    userClear = pyqtSignal()
    userAdd = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        while True:
            self.userClear.emit()
            for (_, user) in self.parent.clientList:
                self.userAdd.emit(str(user))
            time.sleep(1)


class makeThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        while True:
            print('wait')

            clientSocket, addr = self.parent.serverSocket.accept()
            print('client accpet addr = ', addr)
            t = mainThread(self, clientSocket, addr)
            t.start()

        self.parent.serverSocket.close()

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
        print('mainThread Thread self = ', parent)
        self.clientSocket = clientSocket
        self.addr = addr
        self.parent = parent

    def makeTimeString(self,Message):
        makeTime = ''
        now = time.localtime()
        makeTime = '%04d/%02d/%02d %02d:%02d:%02d' % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        return '['+makeTime+'] ' + Message

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
                        owner = ''
                        for client in self.parent.parent.clientList:
                            if client[0] == self.clientSocket:
                                owner = client[1]
                        log = self.makeTimeString(f'Chat: {owner} -> {msgList[2]}: {msgList[3]}')
                        self.parent.parent.addLog(log)
                        if msgList[2] == 'all':
                            for client in self.parent.parent.clientList:
                                client[0].send(('Chat/Send/' + clientID + ': ' + msgList[3]).encode())
                        else:
                            for client in self.parent.parent.clientList:
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
                                for client in self.parent.parent.clientList:
                                    if client[1] == msgList[1]:
                                        self.clientSocket.send('Login/Error/이미 접속 중인 아이디입니다.'.encode())
                                        isIdAlready = True
                                if not isIdAlready:
                                    print('add friendlist: ' + msgList[1])
                                    self.parent.parent.clientList.append((self.clientSocket, msgList[1]))
                                    print(self.parent.parent.clientList)
                                    self.clientSocket.send('Login/Success'.encode())
                                    clientID = userId
                                    msg = self.makeTimeString(f'Login: {userId}')
                                    self.parent.parent.addLog(msg)
                            else:
                                self.clientSocket.send('Login/Error/비밀번호가 맞지 않습니다.'.encode())
                elif msgList[0] == 'FriendList':
                    if msgList[1] == 'Get':
                        print('friendList get: ' + str(self.parent.parent.clientList))
                        idList = []
                        for i in self.parent.parent.clientList:
                            idList.append(i[1])
                        self.clientSocket.send(('FriendList/Receive/' + str(idList)).encode())
                elif msgList[0] == 'Signin':
                    if msgList[1] != '' and msgList[2] != '':
                        query = 'INSERT INTO user VALUES (\'' + msgList[1] + '\',\'' + msgList[2] + '\')'
                        cur.execute(query)
                        conn.commit()
                        print('signin: ' + msgList[1])
                        log = self.makeTimeString(f'SignUp: {msgList[1]}')
                        self.parent.parent.addLog(log)

        except ConnectionResetError as e:
            print('Disconnected by ' + self.addr[0], ':', self.addr[1])
            self.clientSocket.close()
            # List에서 빠진 Client의 ID를 제거...
            if (self.clientSocket, clientID) in self.parent.parent.clientList:
                self.parent.parent.clientList.remove((self.clientSocket, clientID))
                log = self.makeTimeString(f'Logout: {userId}')
                self.parent.parent.addLog(log)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = ServerWindow()
    mainWindow.show()
    app.exec_()