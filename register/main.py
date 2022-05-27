import sys
import os
import socket
import cv2
from PyQt5.QtCore import QByteArray, QIODevice
from PyQt5.QtGui import QImage, QPixmap

from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui

def resource_path(relative_path):
    print(relative_path)
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

mainUi = uic.loadUiType("main.ui")[0]


class MainWindow(QMainWindow, mainUi):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.btn_picture.clicked.connect(self.picture)
        self.btn_register.clicked.connect(self.register)

    #def picture(self):
    #    pass

    def register(self):
        name = self.te_name.text()
        print(name)

    def faceImage(self, img):
        # cv2.imshow("aa",img)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # bgr을 rgb로 변환
        h, w, c = img.shape  # 이미지 파일 모양을 return
        qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qImg)
        return pixmap

        pass

    def picture(self):
        self.FileOpen = ""
        #capture = cv2.VideoCapture('sample.mp4')
        try:
            capture = cv2.VideoCapture(0)
        except:
            QMessageBox.warning(self, "Warning", "카메라가 인식되지 않았습니다.")
            return

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 241)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 331)

        text = "Press the ESC key to take a picture."
        font = cv2.FONT_HERSHEY_SIMPLEX
        org = (10, 30)
        while cv2.waitKey(33) < 0:
            ret, frame = capture.read()
            if not ret :
                QMessageBox.warning(self, "Warning", "카메라가 인식되지 않았습니다.")
                return
            orgImage = frame.copy()
            cv2.putText(frame, text, org, font, 0.5, (0, 0, 255), 1)

            cv2.imshow("VideoFrame", frame)
            #cv2.imshow("OrgFrame", orgImage)

        captureImage = orgImage.copy()
        cv2.imwrite("aaa.png", captureImage)
        capture.release()
        cv2.destroyAllWindows()

        pixmap = self.faceImage(captureImage)
        self.lab_picture.setPixmap(pixmap)  # label의 영역에 사진 표시




if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()