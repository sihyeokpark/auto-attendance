import sys
import os
import numpy as np
import cv2
import dlib
from PyQt5.QtCore import QByteArray, QIODevice
from PyQt5.QtGui import QImage, QPixmap

from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui

def resource_path(relative_path):
    print(relative_path)
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

mainUi = uic.loadUiType('./registerFace.ui')[0]

class registerFaceWindow(QDialog, mainUi):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('exon register face')

        self.captureImage = None
        self.captureFlag = False
        self.isLandmark = False
        self.closeFlag = False

        self.btn_picture.clicked.connect(self.picture)
        self.btn_register.clicked.connect(self.register)
        self.rbLandmark.clicked.connect(self.setLandmark)

        self.faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        self.show()

    def setLandmark(self):
        if self.rbLandmark.isChecked():
            self.isLandmark = True
        elif not self.rbLandmark.isChecked():
            self.isLandmark = False

    # 영상 속에서 얼굴 영역을 추출하고 얼굴의 68개 randmarks를 찾아내는 Code..
    def detect(self, gray, frame):
        # 일단, 등록한 Cascade classifier 를 이용 얼굴을 찾음
        faces = self.faceCascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(100, 100),
                                             flags=cv2.CASCADE_SCALE_IMAGE)

        # 얼굴에서 랜드마크를 찾자
        for (x, y, w, h) in faces:
            # 오픈 CV 이미지를 dlib용 사각형으로 변환하고
            dlib_rect = dlib.rectangle(int(x), int(y), int(x + w), int(y + h))
            # 랜드마크 포인트들 지정
            landmarks = np.matrix([[p.x, p.y] for p in self.predictor(frame, dlib_rect).parts()])
            # 원하는 포인트들을 넣는다, 지금은 전부
            landmarks_display = landmarks[0:68]
            # 눈만 = landmarks_display = landmarks[RIGHT_EYE_POINTS, LEFT_EYE_POINTS]

            # 포인트 출력
            for idx, point in enumerate(landmarks_display):
                pos = (point[0, 0], point[0, 1])
                cv2.circle(frame, pos, 2, color=(0, 255, 255), thickness=-1)

        return frame

    def sigle2coupleDigit(self, n):
        s = n
        try:
            if int(n) < 10:
                s = '0' + n
            return s
        except:
            pass

    def reject(self):
        if self.closeFlag:
            super().reject()
        else:
            print("just reject")

    def register(self):
        userName = self.leName.text()
        userGrade = self.sigle2coupleDigit(self.leGrade.text())
        userClass = self.sigle2coupleDigit(self.leClass.text())
        userNumber = self.sigle2coupleDigit(self.leNumber.text())
        # 입력이 되지 않았으면 리턴... 다시 입력하게끔 유도...

        if not self.captureFlag :
            QMessageBox.information(self, 'infomation', '얼굴 사진을 찍어 주세요..')
        elif (userName == None) or (userGrade == None) or (userClass == None) or (userNumber == None):
            QMessageBox.information(self, 'infomation', '인적사항을 적어주세요. (학년, 반, 번호는 숫자로 적어주세요)')
        else:
            fileName = (f'./face_detect/faces/{userName}_{userGrade}{userClass}{userNumber}.jpg')
            self.imwrite(fileName,self.captureImage)
            #cv2.imwrite(f"../face_detect/faces/{userName}_{userGrade}{userClass}{userNumber}.jpg", self.captureImage)  # 한국어는 안됨..
            QMessageBox.information(self, 'infomation', '얼굴 등록이 성공 하였습니다..')
            self.closeFlag = True
            self.close()

    def imwrite(self, filename, img, params=None):
        try:
            ext = os.path.splitext(filename)[1]
            result, n = cv2.imencode(ext, img, params)

            if result:
                with open(filename, mode='w+b') as f:
                    n.tofile(f)
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def faceImage(self, img):
        # cv2.imshow("aa",img)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # bgr을 rgb로 변환
        h, w, c = img.shape  # 이미지 파일 모양을 return
        qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qImg)
        return pixmap

    def picture(self):
        self.FileOpen = ''
        # capture = cv2.VideoCapture('sample.mp4')
        try:
            capture = cv2.VideoCapture(0)
        except:
            QMessageBox.warning(self, 'Warning', '카메라가 인식되지 않았습니다.')
            return

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 241)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 331)

        text = 'Press the ESC key to take a picture.'
        font = cv2.FONT_HERSHEY_SIMPLEX
        org = (10, 30)
        orgImage = None
        while cv2.waitKey(33) < 0:
            ret, frame = capture.read()
            if not ret:
                QMessageBox.warning(self, 'Warning', '카메라가 인식되지 않았습니다.')
                return
            orgImage = frame.copy()

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # 만들어준 얼굴 눈 찾기
            canvas = None
            if self.isLandmark:
                # 그리고 이미지를 그레이스케일로 변환
                canvas = self.detect(gray, frame)
            else:
                canvas = frame.copy()
            # 찾은 이미지 보여주기

            cv2.putText(canvas, text, org, font, 0.5, (0, 0, 255), 1)

            cv2.imshow('VideoFrame', canvas)

        self.captureImage = orgImage.copy()
        self.captureFlag = True

        capture.release()
        cv2.destroyAllWindows()

        pixmap = self.faceImage(self.captureImage)
        self.lab_picture.setPixmap(pixmap)  # label의 영역에 사진 표시


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     mainWindow = registerFaceWindow()
#     mainWindow.show()
#     app.exec_()
