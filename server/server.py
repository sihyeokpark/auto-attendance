import socket
import sqlite3
import time
import os
import sys
import schedule

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic, QtGui

import registerFace
import utils

serverUi = uic.loadUiType('server.ui')[0]
scheduleUi = uic.loadUiType('schedule.ui')[0]

class ScheduleWindow(QDialog, scheduleUi):
    setSchedule = pyqtSignal(int, list, bool)
    initSchedule = pyqtSignal()

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
            self.parent.cursor.execute(f"UPDATE schedule SET Date = '{dateValue}', Time = '{timeValue}', Who = '{whoValue}', Notice = '{noticeValue}' WHERE Id = {rowPosition}")
        else:
            self.parent.twSchedule.insertRow(rowPosition)
            id = 0
            if rowPosition-1 >= 0:
                id = int(self.parent.twSchedule.item(rowPosition-1, 0).text())+1
            self.parent.cursor.execute(f"INSERT INTO schedule VALUES({str(id)}, '{dateValue}', '{timeValue}', '{whoValue}', '{noticeValue}')")
        self.parent.con.commit()

        itemList = [str(rowPosition), dateValue, timeValue, whoValue, noticeValue]
        self.setSchedule.emit(rowPosition, itemList, self.modi)

        # table widget 있는 모든 데이터를 항상 다시 등록 해야됨..
        #이미 등록이 되어있을 경우 추가로 등록하면 안되는 현상 발견..
        # schedule 의 cancel_job() 함수를 호출하여 기존 데이터를 종료 시키고
        # 다시 등록..
        # monday, tuesday, wednesday, thursday, friday, saturday, sunday

        if dateValue == '월요일': self.parent.schedules.append(schedule.every().monday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue)))
        elif dateValue == '화요일': self.parent.schedules.append(schedule.every().tuesday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue)))
        elif dateValue == '수요일': self.parent.schedules.append(schedule.every().wednesday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue)))
        elif dateValue == '목요일': self.parent.schedules.append(schedule.every().thursday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue)))
        elif dateValue == '금요일': self.parent.schedules.append(schedule.every().friday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue)))
        elif dateValue == '토요일': self.parent.schedules.append(schedule.every().saturday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue)))
        elif dateValue == '일요일': self.parent.schedules.append(schedule.every().sunday.at(timeValue).do(self.parent.executeSchedule, (whoValue, noticeValue)))

        self.initSchedule.emit()

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
        ##self.HOST = '192.168.35.82'
        self.HOST = '192.168.35.188'
        self.PORT = 6666

        self.dbFileName = 'schedule.db'
        self.dbFlag = os.path.isfile(self.dbFileName)
        self.con = sqlite3.connect('schedule.db')
        self.cursor = self.con.cursor()
        self.schedules = []
        self.createDb()
        self.initScheduleTable()


        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.HOST, self.PORT))
        self.serverSocket.listen()

        self.btnRegisterFace.clicked.connect(self.registerFace)
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

    def registerFace(self):
        self.hide()
        self.registerWindow = registerFace.registerFaceWindow()
        self.registerWindow.exec()
        self.show()

    @pyqtSlot()
    def initScheduleTable(self):
        rows = self.selectAllDb()
        self.twSchedule.setRowCount(0)
        for i in range(len(rows)):
            print()
            if rows[i][1] == '월요일':
                self.schedules.append(
                    schedule.every().monday.at(rows[i][2]).do(self.executeSchedule, (rows[i][3], rows[i][4])))
            elif rows[i][1] == '화요일':
                self.schedules.append(
                    schedule.every().tuesday.at(rows[i][2]).do(self.executeSchedule, (rows[i][3], rows[i][4])))
            elif rows[i][1] == '수요일':
                self.schedules.append(
                    schedule.every().wednesday.at(rows[i][2]).do(self.executeSchedule, (rows[i][3], rows[i][4])))
            elif rows[i][1] == '목요일':
                self.schedules.append(
                    schedule.every().thursday.at(rows[i][2]).do(self.executeSchedule, (rows[i][3], rows[i][4])))
            elif rows[i][1] == '금요일':
                self.schedules.append(
                    schedule.every().friday.at(rows[i][2]).do(self.executeSchedule, (rows[i][3], rows[i][4])))
            elif rows[i][1] == '토요일':
                self.schedules.append(
                    schedule.every().saturday.at(rows[i][2]).do(self.executeSchedule, (rows[i][3], rows[i][4])))
            elif rows[i][1] == '일요일':
                self.schedules.append(
                    schedule.every().sunday.at(rows[i][2]).do(self.executeSchedule, (rows[i][3], rows[i][4])))
            rowPosition = self.twSchedule.rowCount()
            self.twSchedule.insertRow(rowPosition)
            for j in range(len(rows[i])):
                self.twSchedule.setItem(i, j, QTableWidgetItem(str(rows[i][j])))


    def selectAllDb(self):
        self.cursor.execute("SELECT * FROM schedule")
        rows = self.cursor.fetchall()
        self.con.commit()
        return rows

    def insertDb(value, self):
        self.cursor.execute(f"INSERT INTO schedule VALUES ({str(value[0])}, '{value[1]}', '{value[2]}', '{value[3]}', '{value[4]}')")
        self.con.commit()

    def createDb(self):
        if not self.dbFlag:
            self.cursor.execute("CREATE TABLE schedule(Id int, Date text, Time text, Who text, Notice text)")
            self.con.commit()
            self.dbFlag = True

    def executeSchedule(self, data):
        whoList = data[0].split(',')[:-1]
        for client in self.clientList:
            if client[1] in whoList:
                # print('Schedule/Send/' + data[1])
                # client[0].send(('Schedule/Send/' + data[1]).encode())
                client[0].send((f'Chat/Send/[스케줄] {data[1]}').encode())


    def deleteSchedule(self):
        x = self.twSchedule.selectedIndexes()
        print(self.twSchedule.item(x[0].row(), 0).text())
        self.cursor.execute(f"DELETE FROM schedule WHERE Id={str(self.twSchedule.item(x[0].row(), 0).text())};")
        self.con.commit()
        self.twSchedule.removeRow(x[0].row())
        print(self.schedules)
        schedule.cancel_job(self.schedules[x[0].row()])
        del self.schedules[x[0].row()]



    def registerSchedule(self):
        scheduleWindow = ScheduleWindow(self, False, self.clientList)
        scheduleWindow.setSchedule.connect(self.setItem)
        scheduleWindow.initSchedule.connect(self.initScheduleTable)
        scheduleWindow.exec_()

    def modifySchedule(self):
        x = self.twSchedule.selectedIndexes()
        itemList = [self.twSchedule.item(x[0].row(), 0).text(), self.twSchedule.item(x[0].row(), 1).text(), self.twSchedule.item(x[0].row(), 2).text(), self.twSchedule.item(x[0].row(), 3).text()]
        scheduleWindow = ScheduleWindow(self, True, self.clientList, itemList)
        scheduleWindow.setSchedule.connect(self.setItem)
        scheduleWindow.initSchedule.connect(self.initScheduleTable)
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
                msg = utils.removeBreakText(data)
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
                            self.clientSocket.send(('Chat/Send/' + clientID + ' -> ' + msgList[2] + ': ' + msgList[3]).encode())
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