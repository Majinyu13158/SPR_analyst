# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'designeruoyvqI.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QMainWindow, QMenuBar, QSizePolicy,
    QStackedWidget, QStatusBar, QWidget,QVBoxLayout,QLabel)

class Ui_custom_StackedWidget(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        palette = QPalette()
        brush = QBrush(QColor(85, 255, 127, 255))
        brush.setStyle(Qt.SolidPattern)
        palette.setBrush(QPalette.Active, QPalette.ToolTipBase, brush)
        palette.setBrush(QPalette.Inactive, QPalette.ToolTipBase, brush)
        palette.setBrush(QPalette.Disabled, QPalette.ToolTipBase, brush)
        MainWindow.setPalette(palette)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.stackedWidget.setGeometry(QRect(420, 20, 191, 461))
        self.page_stackedWidget = QWidget()
        self.page_stackedWidget.setObjectName(u"page")
        self.stackedWidget.addWidget(self.page_stackedWidget)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi
#一个自定义的StackedWidget。它的功能是作为一个小图列表代表不同的拟合，类似tracedrawer
class subplot_Of_custom_StackedWidget(QWidget):
    def __init__(self):
        super(QWidget,self).__init__()

class custom_StackedWidget(QStackedWidget,Ui_custom_StackedWidget):
    def __init__(self,Results):
        super(QStackedWidget,self).__init__()
        self.setupUi(self)
        self.results = Results
    def add_new_image(self):
        #在进行一次拟合之后，添加一个小Widget，然后在里面放缩略图片，涉及到一个生成缩略图的算法以及暂时存储图像文件
        #我思路调整一下，把这个小Widget也写成一个类好了
        self_new_widget=QWidget()
        self_new_widget.setObjectName("list_image"+str(self.results.num))
        self_new_widget_layout=QVBoxLayout()

        self_new_widget_image = QWidget()
        self_new_widget_image.setObjectName()
        self_new_widget_image.setGeometry()

        self_new_widget_text = QLabel#这里我想实现一个不点击就像普普通通的Label，一旦点击就出来textedit可以进行编辑
        self_new_widget_text.setObjectName()
        self_new_widget_text.setText()
        self_new_widget_text.setGeometry()


        self.add_widget(self_new_widget)
    def change_image(self):
        #对图像进行修改之后删除原图像，添加上新图像进行更新
    def delete_image(self):
        #删除图像，同时删除该次拟合相关的东西
        #上下文菜单或者鼠标移动过去就旁边显示一个×号
    def select_and_change_tab(self):
        #点击对应的小图进行窗口中间绘图标签页的切换
