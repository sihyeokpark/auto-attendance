import sys
import socket
from PyQt5.QtWidgets import *
from PyQt5 import uic

HOST = '127.0.0.1'
PORT = 6666

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ui_class = uic.loadUiType("main.ui")[0]

class MyWindow(QMainWindow, ui_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_connect.clicked.connect(self.connect)
        self.btn_send.clicked.connect(self.send)

    def connect(self):
        print('connected')
        client_socket.connect((HOST, PORT))

    def send(self):
        print('send message')
        client_socket.send(self.le_chat.toPlainText().encode())

    def receive(self):
        print('receive message')
        msg = client_socket.recv(1024)
        print(msg)
        self.tb_chat.append(msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()