# -*- coding: utf-8 -*-
import socket
import sqlite3
import sys
import schedule

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic, QtGui

import registerFace
import face_detect.makeCsv
import utils
import face_recognition
import cv2
import numpy as np
import os
import time
import csv


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
        print(self.schedules)
        self.videoFlag = False
        self.vidoThread = None
        self.checkPerson = []

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind((self.HOST, self.PORT))
        self.serverSocket.listen()

        self.btn_start.clicked.connect(self.startVideo)
        self.btnRegisterFace.clicked.connect(self.registerFace)
        self.btnLearnFace.clicked.connect(self.learnFace)
        self.btnRegister.clicked.connect(self.registerSchedule)
        self.btnModify.clicked.connect(self.modifySchedule)
        self.btnDelete.clicked.connect(self.deleteSchedule)

        #idRefreshThread = userIDRefresh(self)
        #idRefreshThread.start()

        print('server start')

        makingThread = makeThread(self)
        makingThread.start()

        showingConnectedUsers = showConnectedUsers(self)
        showingConnectedUsers.userClear.connect(self.clearUser)
        showingConnectedUsers.userAdd.connect(self.addUser)
        showingConnectedUsers.start()

        runSchedule = RunSchedule(self)
        runSchedule.start()
        self.setVideoImage()

    def learnFace(self):
        face_detect.makeCsv.makeCsv()
        print('dd')
    def setVideoImage(self):
        self.lbl_video.setPixmap(QtGui.QPixmap("img/video.png"))
    def startVideo(self):
        if not self.videoFlag:
            self.videoFlag = True
            self.btn_start.setText("출석체크 정지")
            self.vidoThread = VideoThread(self)
            self.vidoThread.start()
        else:
            if self.vidoThread != None :
                self.videoFlag = False
                self.btn_start.setText("출석체크 시작")
                self.vidoThread.stop()
                self.setVideoImage()
        pass
    def registerFace(self):
        self.hide()
        self.registerWindow = registerFace.registerFaceWindow()
        self.registerWindow.exec()
        self.show()

    @pyqtSlot()
    def initScheduleTable(self):
        rows = self.selectAllDb()
        self.twSchedule.setRowCount(0)
        print(len(rows))
        for i in range(len(rows)):
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
        whoList = data[0].replace(' ', '').split(',')
        print(whoList)
        print(self.clientList)
        for client in self.clientList:
            if client[1] in whoList:
                # client[0].send((f'Chat/Send/[스케줄] {data[1]}').encode())
                # self.addLog(f'Chat/Send/[스케줄] {data[1]}')
                client[0].send((f'Schedule/Send/[스케줄] {data[1]}').encode())
                self.addLog(f'Schedule/Send/[스케줄] {data[1]}')
                time.sleep(1)


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
        itemList = [self.twSchedule.item(x[0].row(), 0).text(), self.twSchedule.item(x[0].row(), 1).text(), self.twSchedule.item(x[0].row(), 2).text(), self.twSchedule.item(x[0].row(), 3).text(), self.twSchedule.item(x[0].row(), 4).text()]
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

class VideoThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def stop(self):
        self.working = False
        self.quit()
        self.wait(5000)  # 5000ms = 5s
    def run(self):

        self.working = True
        # openCV 카메라를 오픈하는 api
        video_capture = cv2.VideoCapture(0)

        ########################################
        # face_recognition Library를 사용하여
        # 딥러닝 기반으로 제작된 dlib의 최첨단 얼굴 인식 기능을 사용하여 구축 했습니다.
        # 이 모델은 Labeled Faces in the Wild 기준으로 99.38%의 정확도를 가집니다.
        # How to use face_recognition API
        # https://face-recognition.readthedocs.io/en/latest/face_recognition.html

        # 이미지 학습(?) 시간 체크
        start_time = time.time()

        # Load a sample picture and learn how to recognize it.
        path = "face_detect/faces"
        file_list = os.listdir(path)

        imgList = []
        faceEncodingList = []
        faceNameList = []
        encoding = []

        # 얼굴 배열 읽어오기
        openFile = './face_detect/faces/face_detecting.csv'
        with open(openFile, 'r') as f:
            rdr = csv.reader(f)
            for i, line in enumerate(rdr):
                nparr = np.array(line)
                floatarr = nparr.astype(np.float64)
                faceEncodingList.append(floatarr)

        # 이름 배열 읽어오기
        openFile = './face_detect/faces/face_detecting_name.csv'
        with open(openFile, 'r') as f:
            rdr = csv.reader(f)
            for i, line in enumerate(rdr):
                faceNameList.append(''.join(line))

        print(f'읽어오는거: {time.time() - start_time}')

        # Create arrays of known face encodings and their names
        # known_face_encodings = faceEncodingList
        # known_face_names = faceNameList

        known_face_encodings = faceEncodingList
        known_face_names = faceNameList
        ########################################

        # Initialize some variables
        face_locations = []
        face_encodings = []
        face_names = []
        process_this_frame = True
        while self.working:
            ret, frame = video_capture.read()
            if ret < 0:
                print("카메라가 열리지 않았습니다 다시 한번 확인해 주세요.")
                pass

            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Only process every other frame of video to save time
            if process_this_frame:
                # Find all the faces and face encodings in the current frame of video
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                face_names = []
                for face_encoding in face_encodings:
                    # See if the face is a match for the known face(s)
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    name = "Unknown"

                    # # If a match was found in known_face_encodings, just use the first one.
                    # if True in matches:
                    #     first_match_index = matches.index(True)
                    #     name = known_face_names[first_match_index]

                    # Or instead, use the known face with the smallest distance to the new face
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]

                    face_names.append(name)

            process_this_frame = not process_this_frame

            # 인식이 된 최초의 시간을 버퍼에 저장한 후에 이름과 출석 시간을 보여준다..
            # 현재 시간을 알아오는 PYTHON

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                now = time.localtime()
                if not face_names in self.parent.checkPerson:
                    self.parent.checkPerson.append(face_names)
                    self.parent.addLog(f"{time.strftime('%Y.%m.%d: %H:%M:%S', now)} - {face_names} 출석 완료.")
                    # 이거 하루에 한 번 아침에 초기화 시켜줘야함
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 1)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (255, 0, 0), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            # Display the resulting image
            ######cv2.imshow('Video', frame)
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # bgr을 rgb로 변환
            h, w, c = img.shape  # 이미지 파일 모양을 return
            qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(qImg)
            self.parent.lbl_video.setPixmap(pixmap)

            # Hit 'q' on the keyboard to quit!
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Release handle to the webcam
        video_capture.release()
        cv2.destroyAllWindows()
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

# 이거 요청할 때만 주게 바꾸기



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
                try:
                    data = self.clientSocket.recv(1024)
                except:
                    pass
                    # print('빈 메세지: ' + self.addr[0], ':', self.addr[1])

                    # List에서 빠진 Client의 ID를 제거...
                    #if (self.clientSocket, clientID) in self.parent.parent.clientList:
                    #    self.parent.parent.clientList.remove((self.clientSocket, clientID))
                    #    log = self.makeTimeString(f'Logout: {userId}')
                    #    self.parent.parent.addLog(log)
                    #self.clientSocket.close()

                msg = utils.removeBreakText(data)
                if msg == '' :
                    # List에서 빠진 Client의 ID를 제거...
                    if (self.clientSocket, clientID) in self.parent.parent.clientList:
                        self.parent.parent.clientList.remove((self.clientSocket, clientID))
                        log = self.makeTimeString(f'Logout: {userId}')
                        self.parent.parent.addLog(log)
                    self.clientSocket.close()

                #msg = data.decode()
                if msg == '': continue
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
            # List에서 빠진 Client의 ID를 제거...
            if (self.clientSocket, clientID) in self.parent.parent.clientList:
                self.parent.parent.clientList.remove((self.clientSocket, clientID))
                log = self.makeTimeString(f'Logout: {userId}')
                self.parent.parent.addLog(log)
            self.clientSocket.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = ServerWindow()
    mainWindow.show()
    app.exec_()