#这个是controller文件，内含槽函数，用于响应用户在GUI上的操作，主要负责有数据交互的部分
#对于无数据交互的操作，可以在GUI文件中直接实现，如MplCanvas类中的所画的图像的缩放与拖动，没啥特殊的交互逻辑，可以直接在gui中实现
#本文件应该调用GUI文件，以更新GUI上的显示
#本文件应当调用model文件，以得到其中的数据与处理数据的方法

# -*- coding: utf-8 -*-
import spr_gui_main
import spr_app_model_main
from model_data_process.LocalBivariate import model_runner
#from custom_GUINavigationToolbar2QT import NavigationToolbar
from custom_widgets.custom_Dialog_for_MplCanvas_Attribtes_Change import MplCanvas_Attributes_Change
import sys
import json_reader
from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect,
                            QSize, Qt,Slot)
from PySide6.QtGui import (QAction, QBrush, QColor, QFont, QPalette)
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QMainWindow,
                               QMenu, QMenuBar, QSizePolicy, QStatusBar,
                               QTabWidget, QToolBox, QToolButton, QVBoxLayout,
                               QWidget, QFileDialog)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

plt.style.use('mystyle2')

#现编写MyController类，用于响应用户在GUI上的操作
#本类中所有的函数都是槽函数，用于响应用户在GUI上的操作
#注意，gui中的部分信号诸如MplCanvas类中绘制的图像，在使用滚轮进行方法缩小时无需特异扔到controller里响应
#controller主要用于响应需要沟通model的操作
#本类中所有槽函数命名应当遵守下述规范：
#1.槽函数的命名应当以对应控件名开头
#2.槽函数的命名应当含有功能描述
#本类中所有槽函数应当给予注释并遵守下述规范：
#注释说明本函数的功能时
# 1.要说明本函数是哪个控件的槽函数
# 2.说明本函数对应该控件上的哪个操作
# 3.说明本函数的具体功能
# 4.说明本函数的参数的含义
class MyController:

    def __init__(self, view, model):
        self.view = view
        self.model = model
        #self.view.central_widget.custom_tab.dragbuttons[self.view.central_widget.custom_tab.tab_num-2].signal1.connect(self.mainwindow_dragable_button_drag_for_img)
        #self.view.central_widget.custom_tab.signal2.connect(self.tabwidget_connect_mid)
        self.view.central_widget.items_figure[self.view.dock_widget3.treewidget.itmes_figure_count].dragbutton.signal1.connect(self.mainwindow_dragable_button_drag_for_img)
        self.view.dock_widget3.treewidget.signal_for_drag_mid.connect(self.canvaswidget_connect_mid)
        self.connect_monitor = 0
        self.view.dock_widget3.treewidget.signal3.connect(self.window_change)
        self.view.dock_widget3.treewidget.signal_to_central.connect(self.addnewitem)
        self.view.dock_widget3.treewidget.signal_to_tab.connect(self.tabwidget_treewidget_mid)
        self.view.dock_widget3.treewidget.signal_data.connect(self.add_new_data)
        self.view.dock_widget3.treewidget.signal_project_details.connect(self.add_new_project_details)
        #self.view.central_widget.custom_tab.dragbuttons[self.view.central_widget.custom_tab.tab_num-2].signal5.connect(self.new_project)

    @Slot(str)
    def mainwindow_dragable_button_drag_for_img(self, file_path,count):
        # 控件：主窗口拖拽作图按钮
        # 操作：用户拖拽文件到GUI上的操作
        # 功能：得到文件路径，调用model中的方法进行处理，将处理结果显示在GUI上
        # 参数：无
        print(file_path)
        print("testing")
        T_data, Y_data, Y_pred = model_runner(file_path)
        #current_tab = self.view.central_widget.custom_tab.currentWidget()
        #print(current_tab)
        self.view.central_widget.items_figure[count].add_canvas_widget_and_draw(T_data, Y_data, Y_pred)
        self.view.central_widget.items_figure[count].destroy_dragable_button(self.view.central_widget.items_figure[count].dragbutton)
        #self.view.central_widget.custom_tab.priiit(current_tab)


    def canvaswidget_connect_mid(self):
        '''
        控件：centralwidget
        操作：用户点击新建一个绘图
        功能：由于信号与槽机制是连接到具体实例上的，当创建新的控件时对于新生成的控件要重新连接信号与槽，调用此函数进行连接
        参数：无
        :return:
        '''
        self.view.central_widget.items_figure[self.view.dock_widget3.treewidget.itmes_figure_count].dragbutton.signal1.connect(self.mainwindow_dragable_button_drag_for_img)
        print("connected")

    @Slot()
    def tabwidget_connect_mid(self):
        '''
        控件：自定义TabWidget
        操作：用户点击标签页
        功能：由于信号与槽机制是连接到具体实例上的，当创建新的标签页时对于新生成的控件要重新连接信号与槽，调用此函数进行连接
        参数：无
        :return:
        '''
        print("connected")
        self.view.central_widget.custom_tab.dragbuttons[self.view.central_widget.custom_tab.tab_num-1].signal1.connect(self.mainwindow_dragable_button_drag_for_img)
        self.connect_monitor+=1
        print(self.connect_monitor)


    @Slot(str)
    def tabwidget_treewidget_mid(self):
        '''
        控件：自定义TabWidget
        操作：用户点击标签页
        功能：由于信号与槽机制是连接到具体实例上的，当创建新的标签页时对于新生成的控件要重新连接信号与槽，调用此函数进行连接
        参数：无
        :return:
        '''
        print("connected")
        self.view.central_widget.custom_tab.click_for_new_tab2(self)
    @Slot()
    def main_window_dragable_button_click_for_img(self):
        '''
        控件：主窗口拖拽作图按钮
        操作：用户点击按钮的操作
        功能：得到文件路径，调用model中的方法进行处理，将处理结果显示在GUI上
        参数：无
        '''
        print("Button 2 clicked")

    @Slot()
    def on_combobox_currentIndexChanged(self, index):
        print(f"ComboBox selected index: {index}")

    @Slot()
    def custom_tabWidget_click_for_new_tab(self, index):
    #控件：自定义TabWidget
    #操作：用户点击新建标签页
    #功能：新建标签页
    #参数：无
        print(f"TabWidget selected index: {index}")

    @Slot()
    def custom_tabWidget_click_for_delete(self):
    #控件：自定义TabWidget
    #操作：用户右键点击标签页并选择删除
    #功能：删除标签页
    #参数：无
        print("TabWidget delete clicked")

    @Slot()
    def MplCanvas_context_menu(self):
    #控件：MplCanvas类
    #操作：用户右键点击或左键双击
    #功能：弹出上下文菜单
    #参数：无
        print("MplCanvas right clicked")
    @Slot()
    def MplCanvas_context_menu(self):
    #控件：MplCanvas类的修改上下文菜单
    #操作：用户点击上下文菜单的操作
    #功能：弹出对话框，修改图像属性
    #参数：无
        print("MplCanvas context menu clicked")


    @Slot()
    def MplCanvas_setting_change(self):
    #控件：MplCanvas类的修改属性对话框
    #操作：用户修改属性
    #功能：修改图像属性
    #参数：无
        print("MplCanvas setting changed")
    @Slot()
    def MplCanvas_attributes_change(self):
        pass

    @Slot()
    def window_change(self, type, a):
        '''
        控件：左侧停靠窗口的treewidget
        操作：用户点击treewidget中的item
        功能：根据item的内容，修改右侧主窗口的内容
        参数：传入的item
        '''
        print('hiohasd')
        self.view.on_tree_item_clicked(type,a)
    @Slot()
    def addnewitem(self,data_count):
        print('jio')
        #self.view.item_and_centralwidget_dict_addnew(data_count)



    @Slot()
    def add_new_data(self, file_path,data_count):
        print('test1105')
        data=json_reader.json_reader(file_path)
        self.model.add_new_data(data, 'file')
        #这里还要展示一下新建的datatable
        self.view.central_widget.items_data[data_count].data_in_from_json(data)

    @Slot()
    def add_new_project_details(self,project_details_content):
        print('test1106')
        self.model.add_new_project_details(project_details_content)

    @Slot()
    def add_new_figure(self,project_details_content):
        print('test1106')
        self.model.add_new_project_details(project_details_content)

    @Slot()
    def add_new_result(self,project_details_content):
        print('test1106')
        self.model.add_new_project_details(project_details_content)


    @Slot()
    def new_project(self,filepath):
        print('new project')
        data = json_reader.json_reader(filepath)
        print(data)
        calculatedatasource = data["CalculateDataSource"]
        calculatedatatype = data["CalculateDataType"]
        calculateformula = data["CalculateFormula"]
        fittingoptionsdict = data["FittingOptions"]
        calculatedatalist = data["CalculateDataList"]
        #self.view.new_project_dialog()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = spr_gui_main.MainWindow()
    model = spr_app_model_main.Model()
    mycontroller = MyController(mainWindow, model)
    mainWindow.show()
    sys.exit(app.exec())