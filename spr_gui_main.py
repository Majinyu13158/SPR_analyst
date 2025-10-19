#本文件用于实现GUI，是MVC架构中的V，内含view文件
#本文件应该被controller文件调用，以传递信号的方式而controller中槽函数响应的方式实现用户在GUI上的交互
import sys
import os
import json_reader
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QToolBar, QMenuBar, QStatusBar, QDialog, QDialogButtonBox)
from PySide6.QtCore import Qt, Signal, QPoint, Slot, QRect, QSize
from PySide6.QtGui import QPainter, QPen, QAction, QBrush, QColor, QFont, QPalette
from qfluentwidgets import (FluentWindow, PrimaryPushButton, LineEdit, ComboBox, 
                          InfoBar, setTheme, Theme, ScrollArea, 
                          setFont, FluentIcon, NavigationInterface,
                          TreeWidget,  TableWidget)
from qfluentwidgets.common.style_sheet import addStyleSheet
from qfluentwidgets.components.widgets.tab_view import TabWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        
        # 设置窗口主题和字体
        setTheme(Theme.LIGHT)
        setFont("Microsoft YaHei")
        
        self.setWindowTitle("SPR Sensor Analyst")
        self.resize(1200, 800)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # 添加中心绘图窗口（在导航界面之前创建）
        self.central_widget = CentralWidget()
        layout.addWidget(self.central_widget)
        
        # 创建导航界面
        self.navigation = NavigationInterface(self)
        self.navigation.setFixedWidth(200)
        self.addSubInterface(self.central_widget, FluentIcon.CHART, "数据分析")
        
        # 添加状态栏
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        
        # 添加工具栏
        self.tool_bar = QToolBar(self)
        self.addToolBar(self.tool_bar)
        
        # 添加菜单栏
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # 添加左侧停靠窗口
        self.dock_widget3 = DockWidget1()
        self.dock_widget3.setTitleBarWidget(QLabel("项目导航"))
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget3)
        
        # 连接信号
        self.dock_widget3.treewidget.clicked.connect(
            self.dock_widget3.treewidget.mytreeClicked)
        
        # 设置项目和中心部件的映射关系
        self.item_and_centralwidget_dict = {
            self.dock_widget3.treewidget.treeitem_data.item_id: self.central_widget.table_data,
            self.dock_widget3.treewidget.treeitem_figure.item_id: self.central_widget.figure_widget,
            self.dock_widget3.treewidget.treeitem_result.item_id: self.central_widget.table_result,
            self.dock_widget3.treewidget.treeitem_projectdetail.item_id: self.central_widget.table_project_detail
        }
        
        # 连接其他信号
        self.dock_widget3.treewidget.signal_to_central.connect(
            self.item_and_centralwidget_dict_addnew)
        self.dock_widget3.treewidget.context_menu_requested.connect(
            self.show_context_menu)
            
        # 创建上下文菜单
        self.context_menu = ContextMenu_Treeitem()
        self.context_menu.change_connection.triggered.connect(
            self.open_relation_dialog)
            
        # 创建连接对话框
        self.dialog_connection = Ui_Connection_Dialog()
        self.dialog_connection.signal_to_add_new_project.connect(
            self.add_new_project_item)
        self.dialog_connection.buttonBox.accepted.connect(
            self.handle_dialog_accepted)
            
        # 设置样式
        self.setStyleSheet("""
            MainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                font-family: 'Microsoft YaHei';
            }
            DockWidget {
                border: none;
                background-color: white;
            }
            StatusBar {
                background-color: white;
                border-top: 1px solid #e0e0e0;
            }
            TabWidget {
                border: none;
            }
            TabWidget::pane {
                border: none;
                background-color: white;
            }
            TabWidget::tab-bar {
                alignment: left;
            }
            TabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                background-color: #f5f5f5;
                border: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            TabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #1a73e8;
            }
            TabBar::tab:hover {
                background-color: #e8f0fe;
            }
        """)

    def show_context_menu(self, item, global_pos):
        self.current_item = item
        self.context_menu.exec_(global_pos)

    def open_relation_dialog(self):
        self.dialog_connection.addItems(self.dock_widget3.treewidget.findItems("", Qt.MatchContains | Qt.MatchRecursive))
        self.populate_combobox_with_tree_items()
        if self.dialog_connection.exec() == QDialog.Accepted:
            selected_items = self.dialog_connection.getSelectedItems()
            for selected_item in selected_items:
                for a in self.dock_widget3.treewidget.findItems("", Qt.MatchContains | Qt.MatchRecursive):
                    if a.item_id == selected_item:
                        print('id')

    @Slot(str)
    def add_new_project_item(self, text = None):
        self.dock_widget3.treewidget.add_new_project(text)

    def populate_combobox_with_tree_items(self):
        self.dialog_connection.comboBox_2.clear()
        root = self.dock_widget3.treewidget.item_series
        item_count = root.childCount()
        for i in range(item_count):
            item = root.child(i)
            self.dialog_connection.comboBox_2.addItem(item.text(0))

    @Slot()
    def handle_dialog_accepted(self):
        selected_items = self.dialog_connection.getSelectedItems()
        current_group_text = self.dialog_connection.comboBox_2.currentText()
        root = self.dock_widget3.treewidget.item_series
        b = self.dock_widget3.treewidget.findItems("", Qt.MatchContains | Qt.MatchRecursive)
        for i in range(root.childCount()):
            group_item = root.child(i)
            if group_item.text(0) == current_group_text:
                print(group_item.text(0))
                for item in b:
                    if item.item_id in selected_items:
                        clone_item = item.copy()
                        print(print('id' + str(item.item_id)))
                        group_item.addChild(clone_item)
        self.populate_combobox_with_tree_items()

    def retranslateUi(self):
        treemid=self.dock_widget3.treewidget.headerItem()
        #treemid.setText(0, QCoreApplication.translate("MainWindow",  "红红火火恍恍惚惚哈哈哈哈哈哈哈哈",  None))

    def item_and_centralwidget_dict_addnew(self,type,a):
        #点击新建item，然后新建一个控件，并且把这个控件和item绑定
        if type == 'data':
            self.central_widget.add_new_tablewidget(type,a)
            print('data added')
            self.item_and_centralwidget_dict[self.dock_widget3.treewidget.items_data[a].item_id] = self.central_widget.items_data[a]
            self.central_widget.items_data[a].setItem(1, 0, QTableWidgetItem(self.dock_widget3.treewidget.items_data[self.dock_widget3.treewidget.itmes_data_count-1].text(0)))
            if a >= 2:
                cell = self.central_widget.items_data[a-1].item(1, 0)
                print(self.central_widget.items_data[a-1])
        elif type == 'project_detail':
            self.central_widget.add_new_tablewidget(type,a)
            print('project_detail added')
            self.item_and_centralwidget_dict[self.dock_widget3.treewidget.items_projectdetail[a].item_id] = self.central_widget.items_projectdetail[a]
            self.central_widget.items_projectdetail[a].setItem(1, 0, QTableWidgetItem(self.dock_widget3.treewidget.items_projectdetail[self.dock_widget3.treewidget.itmes_projectdetail_count-1].text(0)))
            if a >= 2:
                cell = self.central_widget.items_projectdetail[a-1].item(1, 0)
                print(self.central_widget.items_projectdetail[a-1])
        elif type == 'result':
            self.central_widget.add_new_tablewidget(type,a)
            print('result added')
            self.item_and_centralwidget_dict[self.dock_widget3.treewidget.items_result[a].item_id] = self.central_widget.items_result[a]
            self.central_widget.items_result[a].setItem(1, 0, QTableWidgetItem(self.dock_widget3.treewidget.items_result[self.dock_widget3.treewidget.itmes_result_count-1].text(0)))
            if a >= 2:
                cell = self.central_widget.items_result[a-1].item(1, 0)
                print(self.central_widget.items_result[a-1])
        elif type == 'figure':
            self.central_widget.add_new_tablewidget(type,a)
            print('figure added')
            self.item_and_centralwidget_dict[self.dock_widget3.treewidget.items_figure[a].item_id] = self.central_widget.items_figure[a]
            #self.central_widget.items_figure[a].setItem(1, 0, QTableWidgetItem(self.dock_widget3.treewidget.items_figure[self.dock_widget3.treewidget.itmes_figure_count-1].text(0)))
            #if a >= 2:
            #    cell = self.central_widget.items_figure[a-1].item(1, 0)
            #    print(self.central_widget.items_figure[a-1])

    def on_tree_item_clicked(self,type,a):

        if type =='figure':
            for key in self.item_and_centralwidget_dict.keys():
                self.item_and_centralwidget_dict[key].hide()
                # if self.dock_widget3.treewidget.items_result[a] in self.item_and_centralwidget_dict.keys():
            self.item_and_centralwidget_dict[a].show()
            self.item_and_centralwidget_dict[a].dragbutton.setText('change')
            print('on_tree_item_clicked')
        else:
            for key in self.item_and_centralwidget_dict.keys():
                self.item_and_centralwidget_dict[key].hide()
            #if self.dock_widget3.treewidget.items_data[a] in self.item_and_centralwidget_dict.keys():
            self.item_and_centralwidget_dict[a + 1].show()
            print('on_tree_item_clicked')

class CanvasWidget(FigureCanvas):
    '''
    这个类比较长，因为里面有用来实现缩放和拖拽的方法
    这几个方法并不涉及任何数据，就放在这里了，没有必要再开一个文件，看的时候把它们折叠起来就顺眼了
    '''
    def __init__(self,T_data, Y_data, Y_pred,parent=None,  width=5, height=4, dpi=100):
        plt.style.use('mystyle2')
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        self.mypainter_windows = []  # Store references to Mypainter windows
        self.testproperty = 1037
        super(CanvasWidget, self).__init__(self.fig)
        self.axes.plot(T_data, Y_data)
        # 初始化鼠标按下的起始坐标和按下状态
        self.startx = 0
        self.starty = 0
        self.mPress = False

        # 设置坐标轴的初始显示范围

        self.axes.autoscale()
        self.axes.set_xlabel('Time/s')
        self.axes.set_ylabel('RU')
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.copy = QAction('复制')
        self.copy.triggered.connect(lambda: print('复制'))
        self.paste = QAction('粘贴')
        self.paste.triggered.connect(lambda: print('粘贴'))
        self.addActions([self.copy, self.paste])

        self.fig.canvas.mpl_connect('scroll_event', self.call_scroll)
        self.fig.canvas.mpl_connect('button_press_event', self.call_move)
        self.fig.canvas.mpl_connect('button_release_event', self.call_move)
        self.fig.canvas.mpl_connect('motion_notify_event', self.call_move)
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
    # 重写 PySide6 的 mouseDoubleClickEvent 方法来检测双击
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:  # 检测左键双击
            print(f"Double-clicked at canvas")
            self.open_custom_dialog()

    # 打开自定义对话框
    def open_custom_dialog(self):
        dialog = MplCanvas_Attributes_Change(self)
        dialog.exec_()  # 打开对话框，阻塞模式

    def call_move(self, event):
        if event.name == 'button_press_event':
            axtemp = event.inaxes
            if axtemp and event.button == 1:  # 左键按下
                self.mPress = True
                self.startx = event.xdata
                self.starty = event.ydata
        elif event.name == 'button_release_event':
            self.mPress = False
        elif event.name == 'motion_notify_event' and self.mPress:
            axtemp = event.inaxes
            if axtemp:
                x_min, x_max = axtemp.get_xlim()
                y_min, y_max = axtemp.get_ylim()
                w = x_max - x_min
                h = y_max - y_min
                mx = event.xdata - self.startx
                my = event.ydata - self.starty
                new_xlim = (x_min - mx, x_min - mx + w)
                new_ylim = (y_min - my, y_min - my + h)
                if new_xlim != axtemp.get_xlim() or new_ylim != axtemp.get_ylim():
                    axtemp.set_xlim(new_xlim)
                    axtemp.set_ylim(new_ylim)
                    self.fig.canvas.draw_idle()  # 实时更新图像

    def call_scroll(self, event):
        axtemp = event.inaxes
        if axtemp:
            x_min, x_max = axtemp.get_xlim()
            y_min, y_max = axtemp.get_ylim()
            x_center = (x_min + x_max) / 2
            y_center = (y_min + y_max) / 2
            
            if event.button == 'up':
                scale_factor = 0.9
            else:
                scale_factor = 1.1
            
            w = (x_max - x_min) * scale_factor
            h = (y_max - y_min) * scale_factor
            
            axtemp.set_xlim([x_center - w/2, x_center + w/2])
            axtemp.set_ylim([y_center - h/2, y_center + h/2])
            self.fig.canvas.draw_idle()

    def on_click(self, event):
        if event.button == 3:  # 右键点击
            print("Right clicked at canvas")
            self.open_custom_dialog()

        # 修改图像属性
        self.AttributeChange = QAction('图像属性修改')
        self.AttributeChange.triggered.connect(lambda: self.params_passer_to_MplCanvas_attributes_change(self))

        # 图像属性修改（详细）
        self.AttributeChangeDetailed = QAction('图像属性修改（详细）')
        self.AttributeChangeDetailed.triggered.connect(lambda: self.params_passer_to_MplCanvas_attributes_change(self))

        if event.inaxes:
            click_radius = 3  # 设置点击半径
            for line in event.inaxes.get_lines():
                xdata, ydata = line.get_data()
                for x, y in zip(xdata, ydata):
                    if ((x - event.xdata) ** 2 + (y - event.ydata) ** 2) ** 0.5 < click_radius:
                        print(f"Clicked point: ({x}, {y}) on line: {line.get_label()}")
                        if event.button == 3:  # 右键点击
                            print("Right click detected!")
                            return
            for collection in event.inaxes.collections:
                for path in collection.get_paths():
                    for offset in collection.get_offsets():
                        if ((offset[0] - event.xdata) ** 2 + (offset[1] - event.ydata) ** 2) ** 0.5 < click_radius:
                            print(f"Clicked point: ({offset[0]}, {offset[1]}) on scatter plot")
                            collection.set_color('black')
                            return


class CanvasWidget_figure(QWidget):
    signal22 = Signal()
    def __init__(self,count,parent=None):
        super().__init__(parent)
        self.dragbutton = DraggableLabel("拖拽文件到这里",count)
        #self.signal22.emit()
        layout = QVBoxLayout(self)
        layout.addWidget(self.dragbutton)
        self.dragbutton.setGeometry(QRect(430, 70, 201, 191))

    def destroy_dragable_button(self, widget):
        widget.hide()
        widget.destroy()

    def add_canvas_widget_and_draw(self,T_data, Y_data, Y_pred):
        canvas_widget = CanvasWidget(T_data, Y_data, Y_pred, self)
        self.layout().addWidget(canvas_widget)
        self.layout().update()


class CentralWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # 创建主布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 创建选项卡部件
        self.tab_widget = TabWidget(self)
        self.layout.addWidget(self.tab_widget)
        
        # 数据表格页
        self.table_data = TableWidget()
        self.table_data.setColumnCount(5)
        self.table_data.setRowCount(0)
        self.table_data.setHorizontalHeaderLabels(["时间", "角度", "反射率", "温度", "备注"])
        self.tab_widget.addTab(self.table_data, "数据表格")
        
        # 图形页
        self.figure_widget = QWidget()
        figure_layout = QVBoxLayout(self.figure_widget)
        figure_layout.setContentsMargins(0, 0, 0, 0)
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        figure_layout.addWidget(self.toolbar)
        figure_layout.addWidget(self.canvas)
        self.tab_widget.addTab(self.figure_widget, "图形显示")
        
        # 结果表格页
        self.table_result = TableWidget()
        self.table_result.setColumnCount(4)
        self.table_result.setRowCount(0)
        self.table_result.setHorizontalHeaderLabels(["参数", "值", "误差", "单位"])
        self.tab_widget.addTab(self.table_result, "分析结果")
        
        # 项目详情页
        self.table_project_detail = TableWidget()
        self.table_project_detail.setColumnCount(2)
        self.table_project_detail.setRowCount(0)
        self.table_project_detail.setHorizontalHeaderLabels(["属性", "值"])
        self.tab_widget.addTab(self.table_project_detail, "项目详情")
        
        # 初始化数据字典
        self.items_data = {}
        self.items_projectdetail = {}
        self.items_result = {}
        self.items_figure = {}
        
        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            TableWidget {
                border: none;
                gridline-color: #e0e0e0;
            }
            TableWidget::item {
                padding: 5px;
            }
            TableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 5px;
                border: none;
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
            }
            QHeaderView::section:checked {
                background-color: #e3f2fd;
            }
        """)

    def add_new_tablewidget(self, type, count):
        if type == 'data':
            self.new_data_table = Custom_TableWidget_data()
            self.layout.addWidget(self.new_data_table)
            self.items_data[count] = self.new_data_table
            self._hide_all_except(type, count)
            self.new_data_table.show()
        elif type == 'project_detail':
            self.new_project_detail_table = Custom_TableWidget_projectdetail()
            self.layout.addWidget(self.new_project_detail_table)
            self.items_projectdetail[count] = self.new_project_detail_table
            self._hide_all_except(type, count)
            self.new_project_detail_table.show()
        elif type == 'result':
            self.new_result_table = Custom_TableWidget_result()
            self.layout.addWidget(self.new_result_table)
            self.items_result[count] = self.new_result_table
            self._hide_all_except(type, count)
            self.new_result_table.show()
        elif type == 'figure':
            self.new_figure = CanvasWidget_figure(count)
            self.layout.addWidget(self.new_figure)
            self.items_figure[count] = self.new_figure
            self._hide_all_except(type, count)
            self.new_figure.show()

    def _hide_all_except(self, type, count):
        """隐藏除了指定类型和计数之外的所有部件"""
        for widgetnum in self.items_data.keys():
            if type != 'data' or widgetnum != count:
                self.items_data[widgetnum].hide()
        for widgetnum in self.items_projectdetail.keys():
            if type != 'project_detail' or widgetnum != count:
                self.items_projectdetail[widgetnum].hide()
        for widgetnum in self.items_result.keys():
            if type != 'result' or widgetnum != count:
                self.items_result[widgetnum].hide()
        for widgetnum in self.items_figure.keys():
            if type != 'figure' or widgetnum != count:
                self.items_figure[widgetnum].hide()


class Custom_TreeWidgetItem_With_Ratiobutton(TreeWidgetItem):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.item_parent_class = None
        self.item_id = None
        self.ratiocheckstate = 0
        
        # 创建一个水平布局来包含单选按钮
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.radio = RadioButton(text)
        layout.addWidget(self.radio)
        
        # 连接单选按钮的信号
        self.radio.toggled.connect(self.onRadioToggled)
        
        # 设置文本
        self.setText(0, text)

    def onRadioToggled(self, checked):
        if checked:
            self.ratiocheckstate = 1
            print(f"{self.item_id} is checked")

class ContextMenu_Treeitem(Menu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.change_connection = Action('调整关联', self)
        self.addAction(self.change_connection)
        self.change_connection.triggered.connect(self.show_change_connection_dialog)

    def show_change_connection_dialog(self):
        self.change_connection_dialog = Dialog_Change_Connection()
        self.change_connection_dialog.exec_()

class Custom_tabWidget(TabWidget):
    signal2 = Signal()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.tabs = {}
        self.tab_num = 1
        self.dragbuttons = {}
        self.init_ui()
        self.tabBarClicked.connect(self.click_for_new_tab1)

    def init_ui(self):
        self.add_new_tab("绘图标签页1")
        self.add_new_tab("新建标签页")

    def add_new_tab(self, title):
        tab = QWidget()
        self.addTab(tab, title)
        self.tabs[self.tab_num] = tab
        
        layout = QVBoxLayout(tab)
        
        dragbutton = DraggableLabel("点击传入文件或拖拽文件作图", tab)
        self.dragbuttons[self.tab_num] = dragbutton
        layout.addWidget(dragbutton)
        
        self.signal2.emit()
        self.tab_num += 1

    def click_for_new_tab1(self, index):
        if index == self.count() - 1:
            self.setTabText(self.tab_num - 2, f"绘图标签页{self.tab_num - 1}")
            self.add_new_tab("新建标签页")

    def click_for_new_tab2(self):
        self.setTabText(self.tab_num - 2, f"绘图标签页{self.tab_num - 1}")
        self.add_new_tab("新建标签页")

    def destroy_dragable_button(self, widget):
        widget.hide()
        widget.destroy()

    def add_canvas_widget_and_draw(self, current_tab, T_data, Y_data, Y_pred):
        canvas_widget = CanvasWidget(T_data, Y_data, Y_pred, self)
        current_tab.layout().addWidget(canvas_widget)
        current_tab.layout().update()

class DraggableLabel(QLabel):
    signal1 = Signal()
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px dashed #cccccc;
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
                color: #666666;
            }
            QLabel:hover {
                background-color: #e8e8e8;
                border-color: #999999;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.signal1.emit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            print(f"File dropped: {file_path}")
            self.signal1.emit()
            event.accept()
        else:
            event.ignore()

class DockWidget1(QWidget):
    def __init__(self):
        super().__init__()
        self.setFeatures(DockWidget.DockWidgetFeature.DockWidgetMovable | 
                        DockWidget.DockWidgetFeature.DockWidgetFloatable)
        
        # 创建树形控件
        self.treewidget = Custom_TreeWidget()
        self.setWidget(self.treewidget)
        
        # 设置样式
        self.setStyleSheet("""
            QDockWidget {
                border: none;
                background: white;
            }
            QDockWidget::title {
                background: #f5f5f5;
                padding: 6px;
                border-bottom: 1px solid #e0e0e0;
            }
        """)

class Custom_TreeWidget(TreeWidget):
    signal_to_central = Signal(str)
    context_menu_requested = Signal(object, object)
    
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setColumnCount(1)
        
        # 创建根节点
        self.item_series = TreeWidgetItem(self)
        self.item_series.setText(0, "项目系列")
        self.item_series.setIcon(0, FluentIcon.FOLDER)
        self.addTopLevelItem(self.item_series)
        
        # 创建子节点
        self.treeitem_data = TreeWidgetItem(self.item_series)
        self.treeitem_data.setText(0, "数据")
        self.treeitem_data.setIcon(0, FluentIcon.TABLE)
        self.treeitem_data.item_id = "data"
        
        self.treeitem_figure = TreeWidgetItem(self.item_series)
        self.treeitem_figure.setText(0, "图形")
        self.treeitem_figure.setIcon(0, FluentIcon.CHART)
        self.treeitem_figure.item_id = "figure"
        
        self.treeitem_result = TreeWidgetItem(self.item_series)
        self.treeitem_result.setText(0, "结果")
        self.treeitem_result.setIcon(0, FluentIcon.CHECKBOX)
        self.treeitem_result.item_id = "result"
        
        self.treeitem_projectdetail = TreeWidgetItem(self.item_series)
        self.treeitem_projectdetail.setText(0, "项目详情")
        self.treeitem_projectdetail.setIcon(0, FluentIcon.INFO)
        self.treeitem_projectdetail.item_id = "project_detail"
        
        # 展开根节点
        self.item_series.setExpanded(True)
        
        # 设置样式
        self.setStyleSheet("""
            QTreeWidget {
                border: none;
                background: white;
            }
            QTreeWidget::item {
                height: 30px;
                padding: 2px;
            }
            QTreeWidget::item:hover {
                background: #f0f0f0;
            }
            QTreeWidget::item:selected {
                background: #e8f0fe;
                color: #1a73e8;
            }
        """)
        
    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            self.context_menu_requested.emit(item, event.globalPos())
            
    def mytreeClicked(self):
        item = self.currentItem()
        if hasattr(item, 'item_id'):
            self.signal_to_central.emit(item.item_id)
            
    def add_new_project(self, text=None):
        if text:
            new_item = TreeWidgetItem(self.item_series)
            new_item.setText(0, text)
            new_item.setIcon(0, FluentIcon.FOLDER)
            new_item.item_id = f"project_{text}"
            self.signal_to_central.emit(new_item.item_id)

class Custom_TreeWidgetItem(TreeWidgetItem):
    def __init__(self, parent=None, custom_data=None, parent_class=None, connection_id=None, item_id=None):
        super().__init__(parent)
        self.parent_class = parent_class
        self.custom_data = custom_data
        self.connection_id = connection_id
        self.item_id = item_id

    def set_custom_data(self, data):
        self.custom_data = data

    def get_custom_data(self):
        return self.custom_data

    def copy(self):
        new_item = Custom_TreeWidgetItem(
            parent=None,
            custom_data=self.custom_data,
            parent_class=self.parent_class,
            connection_id=self.connection_id,
            item_id=self.item_id
        )
        new_item.setText(0, self.text(0))

        # 递归复制所有子项
        for i in range(self.childCount()):
            child = self.child(i)
            new_item.addChild(child.copy())

        return new_item

class Custom_TableWidget(TableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(30)
        self.setRowCount(30)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.verticalScrollBar().valueChanged.connect(self.check_and_add_rows)
        self.horizontalScrollBar().valueChanged.connect(self.check_and_add_columns)
        
        # 设置样式
        self.setStyleSheet("""
            QTableWidget {
                border: none;
                background: white;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background: #e8f0fe;
                color: #1a73e8;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 5px;
                border: none;
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
            }
        """)

    def check_and_add_rows(self):
        if self.verticalScrollBar().value() == self.verticalScrollBar().maximum():
            current_row_count = self.rowCount()
            self.setRowCount(current_row_count + 10)
            for i in range(current_row_count, current_row_count + 10):
                self.setVerticalHeaderItem(i, TableWidgetItem(f"Row {i+1}"))

    def check_and_add_columns(self):
        if self.horizontalScrollBar().value() == self.horizontalScrollBar().maximum():
            current_column_count = self.columnCount()
            self.setColumnCount(current_column_count + 10)
            for i in range(current_column_count, current_column_count + 10):
                self.setHorizontalHeaderItem(i, TableWidgetItem(f"第{i+1}组"))

class Custom_TableWidget_Data(Custom_TableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(['ID', 'Time', 'XValue', 'YValue', 'YPrediction'])
        
        # 初始化上下文菜单
        self.context_menu = Menu(self)
        self.copy_action = Action('复制', self)
        self.paste_action = Action('粘贴', self)
        self.copy_action.triggered.connect(lambda: print('复制'))
        self.paste_action.triggered.connect(lambda: print('粘贴'))
        self.context_menu.addActions([self.copy_action, self.paste_action])
        
        # 设置上下文菜单策略
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, position):
        self.context_menu.exec_(self.mapToGlobal(position))

    def data_in_from_json(self, data):
        self.fillTable(data['CalculateDataList'])

    def fillTable(self, dataList, startRow=0):
        for i, dataPoint in enumerate(dataList):
            baseData = dataPoint.get('BaseData', [])
            combineData = dataPoint.get('CombineData', [])
            self.fillSubTable(baseData, startRow)
            self.fillSubTable(combineData, startRow + len(baseData))

    def fillSubTable(self, subDataList, startRow):
        for i, dataPoint in enumerate(subDataList):
            rowPosition = startRow + i
            self.insertRow(rowPosition)
            self.setItem(rowPosition, 0, TableWidgetItem(str(dataPoint.get('ID', 'N/A'))))
            self.setItem(rowPosition, 1, TableWidgetItem(str(dataPoint.get('XValue', 'N/A'))))
            self.setItem(rowPosition, 2, TableWidgetItem(str(dataPoint.get('YValue', 'N/A'))))

class Custom_TableWidget_ProjectDetail(Custom_TableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setRowCount(9)
        
        headers = [
            "实验编号", "实验时间", "所属项目", "实验人员",
            "实验地点", "实验仪器", "实验方法", "实验样品", "实验目的"
        ]
        
        for i, header in enumerate(headers):
            self.setItem(i, 0, TableWidgetItem(header))

class Custom_TableWidget_Result(Custom_TableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["参数", "值", "误差", "单位"])

class Dialog_Change_Connection(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("调整关联")
        self.resize(300, 200)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.label = QLabel("调整关联")
        self.layout.addWidget(self.label)
        self.button = PrimaryPushButton("确定")
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.accept)

    def accept(self):
        super().accept()



class Connection_Dialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("调整关联")
        self.resize(600, 400)

        self.tabWidget = TabWidget(self)
        self.tab = QWidget()
        self.tabWidget.addTab(self.tab, "Tab 1")

        self.tab_2 = QWidget()
        self.tabWidget.addTab(self.tab_2, "Tab 2")

        self.tree = TreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["数据", "图表", "项目信息", "拟合"])

        layout = QVBoxLayout(self.tab)
        layout.addWidget(self.tree)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.tabWidget)

    def addItems(self, items):
        for item in items:
            self.tree.addTopLevelItem(TreeWidgetItem([item.text(0)]))

class MenuBar(QMenuBar):
    def __init__(self):
        super().__init__()

        # 文件菜单
        file_menu = self.addMenu("文件")
        file_menu.addAction(QAction("新建", self))
        file_menu.addAction(QAction("打开", self))
        file_menu.addAction(QAction("保存", self))
        file_menu.addAction(QAction("另存为", self))
        file_menu.addSeparator()
        file_menu.addAction(QAction("退出", self))

        # 编辑菜单
        edit_menu = self.addMenu("编辑")
        edit_menu.addAction(QAction("剪切", self))
        edit_menu.addAction(QAction("复制", self))
        edit_menu.addAction(QAction("粘贴", self))
        edit_menu.addSeparator()
        edit_menu.addAction(QAction("撤销", self))
        edit_menu.addAction(QAction("重做", self))

        # 视图菜单
        view_menu = self.addMenu("视图")
        view_menu.addAction(QAction("放大", self))
        view_menu.addAction(QAction("缩小", self))
        view_menu.addAction(QAction("重置缩放", self))

        # 帮助菜单
        help_menu = self.addMenu("帮助")
        help_menu.addAction(QAction("关于", self))
        help_menu.addAction(QAction("文档", self))

class ToolBar(QToolBar):
    def __init__(self):
        super().__init__()

        # 添加工具栏按钮
        self.addAction(QAction("新建", self))
        self.addAction(QAction("打开", self))
        self.addAction(QAction("保存", self))
        self.addAction(QAction("另存为", self))
        self.addSeparator()
        self.addAction(QAction("撤销", self))
        self.addAction(QAction("重做", self))

class Ui_Connection_Dialog(QDialog):
    signal_to_add_new_project = Signal(str)
    
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName("Dialog")
        Dialog.resize(800, 600)
        
        self.layout = QVBoxLayout(Dialog)
        
        # 创建选项卡部件
        self.tabWidget = TabWidget(Dialog)
        self.layout.addWidget(self.tabWidget)
        
        # 第一个选项卡
        self.tab = QWidget()
        self.tabWidget.addTab(self.tab, "关联设置")
        
        tab_layout = QVBoxLayout(self.tab)
        
        # 添加树形控件
        self.treeWidget = TreeWidget()
        self.treeWidget.setHeaderLabels(["数据"])
        tab_layout.addWidget(self.treeWidget)
        
        # 添加按钮盒子
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        tab_layout.addWidget(self.buttonBox)
        
        # 第二个选项卡
        self.tab_2 = QWidget()
        self.tabWidget.addTab(self.tab_2, "新建组")
        
        tab2_layout = QVBoxLayout(self.tab_2)
        
        # 添加标签和输入框
        self.label = QLabel("将右侧选中控件关联到选中的组中")
        tab2_layout.addWidget(self.label)
        
        self.label_2 = QLabel("新建并命名一个组：")
        tab2_layout.addWidget(self.label_2)
        
        self.lineEdit = LineEdit()
        tab2_layout.addWidget(self.lineEdit)
        
        self.pushButton = PrimaryPushButton("确认新建")
        self.pushButton.clicked.connect(self.on_new_group)
        tab2_layout.addWidget(self.pushButton)
        
        self.tabWidget.setCurrentIndex(0)

    def on_new_group(self):
        group_name = self.lineEdit.text()
        if group_name:
            self.signal_to_add_new_project.emit(group_name)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle("关联设置")
        self.tabWidget.setTabText(0, "关联设置")
        self.tabWidget.setTabText(1, "新建组")
        self.label.setText("将右侧选中控件关联到选中的组中")
        self.label_2.setText("新建并命名一个组：")
        self.pushButton.setText("确认新建")

    def addItems(self, items):
        for item in items:
            if item.parent_class is None:
                continue
            elif item.parent_class == 'data':
                self.treeWidget.addTopLevelItem(TreeWidgetItem([item.text(0)]))

def set_palette_and_style(main_window):
    palette = QPalette()
    brush = QBrush(QColor(0, 0, 0, 255))
    brush.setStyle(Qt.SolidPattern)
    palette.setBrush(QPalette.Active, QPalette.WindowText, brush)
    brush1 = QBrush(QColor(255, 255, 255, 255))
    brush1.setStyle(Qt.SolidPattern)
    palette.setBrush(QPalette.Active, QPalette.Button, brush1)
    palette.setBrush(QPalette.Active, QPalette.Light, brush1)
    palette.setBrush(QPalette.Active, QPalette.Midlight, brush1)
    brush2 = QBrush(QColor(127, 127, 127, 255))
    brush2.setStyle(Qt.SolidPattern)
    palette.setBrush(QPalette.Active, QPalette.Dark, brush2)
    brush3 = QBrush(QColor(170, 170, 170, 255))
    brush3.setStyle(Qt.SolidPattern)
    palette.setBrush(QPalette.Active, QPalette.Mid, brush3)
    palette.setBrush(QPalette.Active, QPalette.Text, brush)
    palette.setBrush(QPalette.Active, QPalette.BrightText, brush1)
    palette.setBrush(QPalette.Active, QPalette.ButtonText, brush)
    palette.setBrush(QPalette.Active, QPalette.Base, brush1)
    palette.setBrush(QPalette.Active, QPalette.Window, brush1)
    palette.setBrush(QPalette.Active, QPalette.Shadow, brush)
    palette.setBrush(QPalette.Active, QPalette.AlternateBase, brush1)
    brush4 = QBrush(QColor(255, 255, 220, 255))
    brush4.setStyle(Qt.SolidPattern)
    palette.setBrush(QPalette.Active, QPalette.ToolTipBase, brush4)
    palette.setBrush(QPalette.Active, QPalette.ToolTipText, brush)
    brush5 = QBrush(QColor(0, 0, 0, 127))
    brush5.setStyle(Qt.SolidPattern)
    palette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush5)
    palette.setBrush(QPalette.Active, QPalette.Accent, brush1)
    palette.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
    palette.setBrush(QPalette.Inactive, QPalette.Button, brush1)
    palette.setBrush(QPalette.Inactive, QPalette.Light, brush1)
    palette.setBrush(QPalette.Inactive, QPalette.Midlight, brush1)
    palette.setBrush(QPalette.Inactive, QPalette.Dark, brush2)
    palette.setBrush(QPalette.Inactive, QPalette.Mid, brush3)
    palette.setBrush(QPalette.Inactive, QPalette.Text, brush)
    palette.setBrush(QPalette.Inactive, QPalette.BrightText, brush1)
    palette.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
    palette.setBrush(QPalette.Inactive, QPalette.Base, brush1)
    palette.setBrush(QPalette.Inactive, QPalette.Window, brush1)
    palette.setBrush(QPalette.Inactive, QPalette.Shadow, brush)
    palette.setBrush(QPalette.Inactive, QPalette.AlternateBase, brush1)
    palette.setBrush(QPalette.Inactive, QPalette.ToolTipBase, brush4)
    palette.setBrush(QPalette.Inactive, QPalette.ToolTipText, brush)
    brush6 = QBrush(QColor(127, 127, 127, 127))
    brush6.setStyle(Qt.SolidPattern)
    palette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush6)
    palette.setBrush(QPalette.Inactive, QPalette.Accent, brush1)

    main_window.setPalette(palette)
    font = QFont()
    font.setPointSize(13)
    main_window.setFont(font)
    main_window.setWindowOpacity(1.0)
    main_window.setStyleSheet("background=rgb(255, 255, 255)")
    main_window.setIconSize(QSize(24, 24))
    main_window.setAnimated(True)
    main_window.setTabShape(QTabWidget.TabShape.Rounded)

def change_connection(item1, item2, connectionid):
    '''
    根据connectionid的调整来判断是否关联，如果id相同那么就是关联的
    感觉这里的内容挺涉及数据结构的知识，我得补一补
    '''
    change_connection_dialog = Dialog_Change_Connection()
    item1.conncectionid = connectionid
    item2.conncectionid = connectionid


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())