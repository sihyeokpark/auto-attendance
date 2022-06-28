import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic

form_class = uic.loadUiType('test.ui')[0]


class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        #self.tb_user.append("test")
        for _ in range(100):
            self.tb_user.clear()
        '''
        ## table widget Test Code
        self.tableWidget.setRowCount(3)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers) #편집을 못하게 옵션질.
        self.tableWidget.setItem(0, 0, QTableWidgetItem('A'))
        self.tableWidget.setItem(1, 0, QTableWidgetItem('B'))
        self.tableWidget.setItem(2, 0, QTableWidgetItem('C'))

        self.tableWidget.setItem(0, 1, QTableWidgetItem('A1'))
        self.tableWidget.setItem(1, 1, QTableWidgetItem('B1'))
        self.tableWidget.setItem(2, 1, QTableWidgetItem('C1'))

        self.tableWidget.setItem(0, 2, QTableWidgetItem('A2'))
        self.tableWidget.setItem(1, 2, QTableWidgetItem('B2'))
        self.tableWidget.setItem(2, 2, QTableWidgetItem('C2'))

        for i in range(3):
            print(i, "%s" % self.tableWidget.item(i, 0).text())
        '''
if __name__ == '__main__':
    app = QApplication(sys.argv)
    mywindow = MyWindow()
    mywindow.show()
    app.exec_()