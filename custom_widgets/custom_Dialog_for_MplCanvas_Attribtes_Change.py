# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '半成品图像属性修改KQdxSu.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtWidgets import ( QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QDoubleSpinBox,
    QLabel, QSizePolicy, QVBoxLayout, QWidget,QColorDialog,QPushButton)
from PySide6.QtCore import (QCoreApplication,
    QMetaObject, QObject, QPoint, QRect)
from PySide6.QtWidgets import (QApplication, QSizePolicy, QTabWidget, QWidget)

'''class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.resize(640, 404)
        self.verticalLayoutWidget = QWidget(Dialog)
        self.verticalLayoutWidget.setGeometry(QRect(0, 0, 225, 381))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.label)
        self.label_2 = QLabel(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.label_2)
        self.doubleSpinBox = QDoubleSpinBox(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.doubleSpinBox)
        self.verticalLayout_2 = QVBoxLayout()
        self.label_4 = QLabel(self.verticalLayoutWidget)
        self.verticalLayout_2.addWidget(self.label_4)
        self.doubleSpinBox_2 = QDoubleSpinBox(self.verticalLayoutWidget)
        self.verticalLayout_2.addWidget(self.doubleSpinBox_2)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.label_3 = QLabel(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.label_3)
        self.lineStyleComboBox = QComboBox(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.lineStyleComboBox)
        self.verticalLayoutWidget_3 = QWidget(Dialog)
        self.verticalLayoutWidget_3.setGeometry(QRect(460, 0, 181, 221))
        self.verticalLayout_3 = QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.verticalLayoutWidget_3)
        self.verticalLayout_3.addWidget(self.label_5)
        self.checkBox = QCheckBox(self.verticalLayoutWidget_3)
        self.verticalLayout_3.addWidget(self.checkBox)
        self.verticalLayoutWidget_4 = QWidget(Dialog)
        self.verticalLayoutWidget_4.setGeometry(QRect(240, 0, 211, 131))
        self.verticalLayout_4 = QVBoxLayout(self.verticalLayoutWidget_4)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_6 = QLabel(self.verticalLayoutWidget_4)
        self.verticalLayout_4.addWidget(self.label_6)
        self.comboBox = QComboBox(self.verticalLayoutWidget_4)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.verticalLayout_4.addWidget(self.comboBox)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QRect(450, 350, 156, 24))
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.retranslateUi(Dialog)
        QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"\u5feb\u6377\u4fee\u6539", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"\u7ebf\u6761\u7c97\u7ec6/\u6563\u70b9\u5927\u5c0f", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"\u989c\u8272", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"\u7ebf\u6761\u7c7b\u578b", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"\u9009\u62e9\u5e94\u7528\u5bf9\u8c61", None))
        self.checkBox.setText(QCoreApplication.translate("Dialog", u"CheckBox", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"\u5176\u4ed6\u56fe\u50cf\u5c5e\u6027\u4fee\u6539", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("Dialog", u"\u4fee\u65391", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("Dialog", u"\u4fee\u65392", None))


class Dialog_for_MplCanvas_Attributes_Changes(QDialog, Ui_Dialog):
    def __init__(self, current_MplCanvas):
        super(Dialog_for_MplCanvas_Attributes_Changes, self).__init__()
        self.setupUi(self)
        self.current_MplCanvas = current_MplCanvas
        self.doubleSpinBox.valueChanged.connect(self.update_line_width)
        self.doubleSpinBox_2.valueChanged.connect(self.update_line_width)
        self.colorButton = QPushButton("Change Line Color", self)
        self.colorButton.clicked.connect(self.open_color_dialog)
        self.verticalLayout_3.addWidget(self.colorButton)
        self.lineStyleComboBox.addItems(['-', '--', '-.', ':'])
        self.lineStyleComboBox.currentIndexChanged.connect(self.update_line_style)

    def update_line_width(self):
        new_width = self.doubleSpinBox.value()
        for line in self.current_MplCanvas.axes.get_lines():
            line.set_linewidth(new_width)
        self.current_MplCanvas.draw_idle()

    def open_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.update_line_color(color)

    def update_line_color(self, color):
        for line in self.current_MplCanvas.axes.get_lines():
            line.set_color(color.name())
        self.current_MplCanvas.draw_idle()

    def update_line_style(self):
        new_style = self.lineStyleComboBox.currentText()
        for line in self.current_MplCanvas.axes.get_lines():
            line.set_linestyle(new_style)
        self.current_MplCanvas.draw_idle()
def MplCanvas_Attributes_Change(current_MplCanvas):
    Mypainter = Dialog_for_MplCanvas_Attributes_Changes(current_MplCanvas)
    Mypainter.show()
    current_MplCanvas.mypainter_windows.append(Mypainter)  # Store reference





class Ui_Tab_for_graph_settings(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(450, 600)
        self.tabWidget = QTabWidget(Form)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 0, 450, 600))
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.tabWidget.addTab(self.tab_3, "")




        self.retranslateUi(Form)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("Form", u"\u56fe\u8868\u5916\u89c2", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("Form", u"\u62df\u5408\u9009\u9879\u8bbe\u7f6e\u4e0e\u6570\u636e\u96c6\u5904\u7406", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("Form", u"\u5176\u4ed6", None))
    # retranslateUi
'''
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QVBoxLayout, QTabWidget, QWidget, QDoubleSpinBox,
    QComboBox, QPushButton, QColorDialog, QCheckBox, QDialogButtonBox)
from PySide6.QtCore import QRect, QCoreApplication


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.resize(640, 404)

        # 新建 QTabWidget，并添加到 Dialog
        self.tabWidget = QTabWidget(Dialog)
        self.tabWidget.setGeometry(QRect(0, 0, 640, 350))

        # 创建第一个 tab，并将原有的控件转移到该 tab
        self.tab1 = QWidget()
        self.verticalLayoutWidget = QWidget(self.tab1)
        self.verticalLayoutWidget.setGeometry(QRect(0, 0, 225, 381))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.label)
        self.label_2 = QLabel(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.label_2)
        self.doubleSpinBox = QDoubleSpinBox(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.doubleSpinBox)
        self.verticalLayout_2 = QVBoxLayout()
        self.label_4 = QLabel(self.verticalLayoutWidget)
        self.verticalLayout_2.addWidget(self.label_4)
        self.doubleSpinBox_2 = QDoubleSpinBox(self.verticalLayoutWidget)
        self.verticalLayout_2.addWidget(self.doubleSpinBox_2)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.label_3 = QLabel(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.label_3)
        self.lineStyleComboBox = QComboBox(self.verticalLayoutWidget)
        self.verticalLayout.addWidget(self.lineStyleComboBox)

        # 将第一个 tab 添加到 tabWidget
        self.tabWidget.addTab(self.tab1, "Tab 1: Controls")

        # 创建第二个 tab（可以自行扩展）
        self.tab2 = QWidget()
        self.verticalLayoutWidget_2 = QWidget(self.tab2)
        self.verticalLayoutWidget_2.setGeometry(QRect(460, 0, 181, 221))
        self.verticalLayout_3 = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.verticalLayoutWidget_2)
        self.verticalLayout_3.addWidget(self.label_5)
        self.checkBox = QCheckBox(self.verticalLayoutWidget_2)
        self.verticalLayout_3.addWidget(self.checkBox)

        self.tabWidget.addTab(self.tab2, "Tab 2: Options")

        # 创建第三个 tab（可以自行扩展）
        self.tab3 = QWidget()
        self.verticalLayoutWidget_3 = QWidget(self.tab3)
        self.verticalLayoutWidget_3.setGeometry(QRect(240, 0, 211, 131))
        self.verticalLayout_4 = QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_6 = QLabel(self.verticalLayoutWidget_3)
        self.verticalLayout_4.addWidget(self.label_6)
        self.comboBox = QComboBox(self.verticalLayoutWidget_3)
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.verticalLayout_4.addWidget(self.comboBox)

        self.tabWidget.addTab(self.tab3, "Tab 3: Additional Settings")

        # ButtonBox remains outside of the tabWidget
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QRect(450, 350, 156, 24))
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)

        self.retranslateUi(Dialog)
        QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"\u5feb\u6377\u4fee\u6539", None))
        self.label_2.setText(
            QCoreApplication.translate("Dialog", u"\u7ebf\u6761\u7c97\u7ec6/\u6563\u70b9\u5927\u5c0f", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"\u989c\u8272", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"\u7ebf\u6761\u7c7b\u578b", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"\u9009\u62e9\u5e94\u7528\u5bf9\u8c61", None))
        self.checkBox.setText(QCoreApplication.translate("Dialog", u"CheckBox", None))
        self.label_6.setText(
            QCoreApplication.translate("Dialog", u"\u5176\u4ed6\u56fe\u50cf\u5c5e\u6027\u4fee\u6539", None))
        self.comboBox.setItemText(0, QCoreApplication.translate("Dialog", u"\u4fee\u65391", None))
        self.comboBox.setItemText(1, QCoreApplication.translate("Dialog", u"\u4fee\u65392", None))

        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab1),
                                  QCoreApplication.translate("Form", u"\u56fe\u8868\u5916\u89c2", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab2), QCoreApplication.translate("Form",
                                                                                                 u"\u62df\u5408\u9009\u9879\u8bbe\u7f6e\u4e0e\u6570\u636e\u96c6\u5904\u7406",
                                                                                                 None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab3),
                                  QCoreApplication.translate("Form", u"\u5176\u4ed6", None))


class Dialog_for_MplCanvas_Attributes_Changes(QDialog, Ui_Dialog):
    def __init__(self, current_MplCanvas):
        super(Dialog_for_MplCanvas_Attributes_Changes, self).__init__()
        self.setupUi(self)
        self.current_MplCanvas = current_MplCanvas
        self.doubleSpinBox.valueChanged.connect(self.update_line_width)
        self.doubleSpinBox_2.valueChanged.connect(self.update_line_width)
        self.colorButton = QPushButton("Change Line Color", self)
        self.colorButton.clicked.connect(self.open_color_dialog)
        self.verticalLayout_3.addWidget(self.colorButton)
        self.lineStyleComboBox.addItems(['-', '--', '-.', ':'])
        self.lineStyleComboBox.currentIndexChanged.connect(self.update_line_style)

    def update_line_width(self):
        new_width = self.doubleSpinBox.value()
        for line in self.current_MplCanvas.axes.get_lines():
            line.set_linewidth(new_width)
        self.current_MplCanvas.draw_idle()

    def open_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.update_line_color(color)

    def update_line_color(self, color):
        for line in self.current_MplCanvas.axes.get_lines():
            line.set_color(color.name())
        self.current_MplCanvas.draw_idle()

    def update_line_style(self):
        new_style = self.lineStyleComboBox.currentText()
        for line in self.current_MplCanvas.axes.get_lines():
            line.set_linestyle(new_style)
        self.current_MplCanvas.draw_idle()


def MplCanvas_Attributes_Change(current_MplCanvas):
    Mypainter = Dialog_for_MplCanvas_Attributes_Changes(current_MplCanvas)
    Mypainter.show()
    current_MplCanvas.mypainter_windows.append(Mypainter)  # Store reference


# 测试代码

