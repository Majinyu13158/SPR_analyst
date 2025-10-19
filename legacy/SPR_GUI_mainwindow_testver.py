# -*- coding: utf-8 -*-
from model_data_process.LocalBivariate import model_runner
#from custom_GUINavigationToolbar2QT import NavigationToolbar
from custom_widgets.custom_Dialog_for_MplCanvas_Attribtes_Change import MplCanvas_Attributes_Change
import sys

from PySide6.QtCore import (QCoreApplication, QMetaObject, QRect,
                            QSize, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QFont, QPalette)
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QMainWindow,
                               QMenu, QMenuBar, QSizePolicy, QStatusBar,
                               QTabWidget, QToolBox, QToolButton, QVBoxLayout,
                               QWidget, QFileDialog)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

'''okay, 现在的逻辑是创建了 resultfigure 类，又定义了mpl类并且有 mpl 类的实例作为 resultfigure 的属性。mpl是一个qt和matplotlib相结合
的产物，它内部进行了画布与坐标轴的创建，同时是一个gui控件，在Mainwindow里有一个字典，用于存储resultfigure的实例和对应的序号，每次拖拽作图时
，会序号加一并对应上一个新的resultfigure实例，然后将这个实例的mpl实例作为一个控件添加到当前tab里，要注意的的是在添加mpl控件的时候先加了一个
qwidget控件再把mpl控件加到这个qwidget里，通过控制qwidget来控制mpl控件的位置和大小，以此解决mpl直接上时的布局被自动设置不能调整的问题。
整体思路简而言之九十定义resultfigure类含有图（mpl）、图的名字、对应数据、别的东西作为总的图形管理的类'''


plt.style.use('mystyle2')


class MplCanvas(FigureCanvas):
    def __init__(self, parent, width=1, height=1, dpi=100):
        plt.style.use('mystyle2')
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.subplots()
        self.mypainter_windows = []  # Store references to Mypainter windows
        self.testproperty = 1037
        super(MplCanvas, self).__init__(self.fig)

        # 初始化鼠标按下的起始坐标和按下状态
        self.startx = 0
        self.starty = 0
        self.mPress = False

        # 设置坐标轴的初始显示范围
        self.axes.set_xlim(0, 10)
        self.axes.set_ylim(0, 10)
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


    # 其他现有方法...


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
            w = x_max - x_min
            h = y_max - y_min
            curx = event.xdata
            cury = event.ydata
            curXposition = (curx - x_min) / w
            curYposition = (cury - y_min) / h
            if event.button == 'down':  # 滚轮向下滚动
                w = w * 1.1
                h = h * 1.1
            elif event.button == 'up':  # 滚轮向上滚动
                w = w / 1.1
                h = h / 1.1
            newx = curx - w * curXposition
            newy = cury - h * curYposition
            new_xlim = (newx, newx + w)
            new_ylim = (newy, newy + h)
            if new_xlim != axtemp.get_xlim() or new_ylim != axtemp.get_ylim():
                axtemp.set_xlim(new_xlim)
                axtemp.set_ylim(new_ylim)
                self.fig.canvas.draw_idle()
                # 实时更新图像

    def params_passer_to_MplCanvas_attributes_change(self, current_MplCanvas):
        MplCanvas_Attributes_Change(current_MplCanvas)


    def on_click(self, event):

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
                            self.addActions([self.AttributeChange])
                            self.addActions([self.AttributeChangeDetailed])
                            return
            for collection in event.inaxes.collections:
                for path in collection.get_paths():
                    for offset in collection.get_offsets():
                        if ((offset[0] - event.xdata) ** 2 + (offset[1] - event.ydata) ** 2) ** 0.5 < click_radius:
                            print(f"Clicked point: ({offset[0]}, {offset[1]}) on scatter plot")
                            collection.set_color('black')
                            self.fig.canvas.draw_idle()
                            self.addActions([self.AttributeChange])
                            return
class ResultFigure():
    def __init__(self,parent, name):
        self.MplCanvas = MplCanvas(parent, width=7, height=5, dpi=100)
        #self.toolbar = NavigationToolbar(self.MplCanvas, parent)
        self.name = name

# 定义一个 DraggableLabel 类，用于实现可拖拽的标签
class DraggableLabel(QLabel):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setAcceptDrops(True)
        self.mousePressPosition = None
        print(f"Parent object name: {parent.objectName()}")

    # 鼠标按下事件处理
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "",
                                                       "All Files (*);;Text Files (*.txt);;Image Files (*.png *.jpg *.gif);;*.xlsx")

            # 如果用户选择了文件，打印出文件路径
            if file_path:
                T_data, Y_data, Y_pred = model_runner(file_path)
                window.num_drag += 1
                print(window.num_drag)
                window.ResultFigures[window.num_drag] = ResultFigure(self.parent,{file_path})
                # 看来这里的self.parent是指的是Draggable实例的父类，也就是tab，也就是类里定义时self指实例本身

                window.ResultFigures[window.num_drag].MplCanvas.setGeometry(QRect(0, 200, 900, 300))
                window.ResultFigures[window.num_drag].MplCanvas.axes.clear()
                for i in range(7):
                    window.ResultFigures[window.num_drag].MplCanvas.axes.scatter(T_data[:, i], Y_data[:, i],
                                                                                  label='Data')
                    window.ResultFigures[window.num_drag].MplCanvas.axes.plot(T_data[:, i], Y_pred[:, i],
                                                                              label='Fit')
                window.ResultFigures[window.num_drag].MplCanvas.axes.legend(['Data', 'Fit'])
                window.ResultFigures[window.num_drag].MplCanvas.lower()

                current_tab = window.tabWidget.currentWidget()
                print(current_tab.objectName())
                layout = current_tab.layout()
                midwidget_for_mpl = QWidget(current_tab)
                layout.addWidget(midwidget_for_mpl)

                toolbar = NavigationToolbar(window.ResultFigures[window.num_drag].MplCanvas)
                layout.addWidget(toolbar)
                toolbar.addAction("新建")
                midwidget_for_mpl.setLayout(QVBoxLayout())
                midwidget_for_mpl.layout().addWidget(window.ResultFigures[window.num_drag].MplCanvas)
                layout.addWidget(window.ResultFigures[window.num_drag].MplCanvas)

                window.ResultFigures[window.num_drag].MplCanvas.resize(300, 100)
                # current_text = window.label_4.text()
                # new_text = current_text + window.ResultFigures[window.num_drag].name + '(' + str(window.num_drag) + ")" + '\n'
                # window.label_4.setText(new_text)
        elif event.button() == Qt.RightButton:
            self.LabelStateChangeed()
        self.hide()

    # 鼠标移动事件处理


    # 标签状态改变处理
    def LabelStateChangeed(self):
        self.setText("已作图 ")

    # 拖拽进入事件处理
    def dragEnterEvent(self, event):
        event.accept()
    # 拖拽放下事件处理
    def dropEvent(self,event,num_drag=None):
        for url in event.mimeData().urls():
            print('Dropped file path: {0}'.format(url.toLocalFile()))
        self.LabelStateChangeed()
        T_data, Y_data, Y_pred = model_runner(format(url.toLocalFile()))
        window.num_drag += 1
        print(window.num_drag)
        window.ResultFigures[window.num_drag] = ResultFigure(self.parent,format(url.toLocalFile()))
        #看来这里的self.parent是指的是Draggable实例的父类，也就是tab，也就是类里定义时self指实例本身
        window.ResultFigures[window.num_drag].MplCanvas.setGeometry(QRect(0, 200, 900, 300))
        window.ResultFigures[window.num_drag].MplCanvas.axes.clear()
        for i in range(7):
            window.ResultFigures[window.num_drag].MplCanvas.axes.scatter(T_data[:,i], Y_data[:,i],label='Data')
            window.ResultFigures[window.num_drag].MplCanvas.axes.plot(T_data[:,i], Y_pred[:,i], label='Fit')
        window.ResultFigures[window.num_drag].MplCanvas.axes.legend(['Data', 'Fit'])
        window.ResultFigures[window.num_drag].MplCanvas.axes.legend(frameon=False,fontsize = 10)
        window.ResultFigures[window.num_drag].MplCanvas.lower()

        current_tab = window.tabWidget.currentWidget()
        print(current_tab.objectName())
        layout = current_tab.layout()
        midwidget_for_mpl = QWidget(current_tab)
        layout.addWidget(midwidget_for_mpl)

        toolbar = NavigationToolbar(window.ResultFigures[window.num_drag].MplCanvas)
        layout.addWidget(toolbar)
        toolbar.addAction("新建")
        midwidget_for_mpl.setLayout(QVBoxLayout())
        midwidget_for_mpl.layout().addWidget(window.ResultFigures[window.num_drag].MplCanvas)
        layout.addWidget(window.ResultFigures[window.num_drag].MplCanvas)

        window.ResultFigures[window.num_drag].MplCanvas.resize(300,100)
        #current_text = window.label_4.text()
        #new_text = current_text + window.ResultFigures[window.num_drag].name + '(' + str(window.num_drag) + ")" + '\n'
        #window.label_4.setText(new_text)
        self.hide()

class custom_tabWidget(QTabWidget):
    def __init__(self,parent):
        super().__init__()
        self.init_ui()
        self.tabBarClicked.connect(self.click_for_new_tab)
    tabs={}
    tab_num = 0

    def init_ui(self):
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.addTab(self.tab1,"绘图标签页1")#这里的绿字和objectname是一回事吗？
        self.addTab(self.tab2,"新建标签页")
        self.tabs[0] = self.tab1
        self.tabs[1] = self.tab2
        self.tab_num = 2
        self.midwidget = QWidget(self.tab1)  # 中介控件，用于放置其他控件
        self.dragbutton = DraggableLabel("点击传入文件或拖拽文件作图", self.midwidget)
        # self.label1 = QLabel("label1", self.midwidget)

        layout = QVBoxLayout(self.tab1)
        layout.addWidget(self.midwidget)
        self.midwidget.setLayout(QVBoxLayout())
        self.midwidget.layout().addWidget(self.dragbutton)
        self.dragbutton.setGeometry(QRect(430, 70, 201, 191))
        self.midwidget = QWidget(self.tab1)  # 中介控件，用于放置其他控件

        self.midwidget2 = QWidget(self.tab2)  # 中介控件，用于放置其他控件
        self.dragbutton = DraggableLabel("点击传入文件或拖拽文件作图", self.midwidget2)
        layout2 = QVBoxLayout(self.tab2)
        layout2.addWidget(self.midwidget2)
        self.midwidget2.setLayout(QVBoxLayout())
        self.midwidget2.layout().addWidget(self.dragbutton)
        self.dragbutton.setGeometry(QRect(430, 70, 201, 191))
        self.midwidget2 = QWidget(self.tab2)
        #self.tab1.num和index是相符的，实际上的标签页数量是index最大值也即是tab_num+1


    def click_for_new_tab(self,index):
        if index == self.count()-1:
            print("Click for new")
            self.tabnew = QWidget()
            self.tabs[self.tab_num]=self.tabnew#添加进字典进行管理
            self.tab_num += 1#标签页数量加1
            self.tabnew.setObjectName("tab"+str(self.tab_num))#设置objectname
            self.addTab(self.tabnew,"新建标签页")#实装新标签页并添加显示的文本
            self.setTabText(self.tab_num-2, "绘图标签页"+str(self.tab_num-1))#设置前一个标签页的文本

            self.midwidget = QWidget(self.tabnew)#中介控件，用于放置其他控件
            self.dragbutton = DraggableLabel("点击传入文件或拖拽文件作图", self.midwidget)
            #self.label1 = QLabel("label1", self.midwidget)

            layout = QVBoxLayout(self.tabnew)
            print("layout created")
            layout.addWidget(self.midwidget)
            self.midwidget.setLayout(QVBoxLayout())
            #self.midwidget.layout().addWidget(self.label1)
            #self.label1.setGeometry(QRect(230, 70, 201, 191))
            self.midwidget.layout().addWidget(self.dragbutton)
            self.dragbutton.setGeometry(QRect(430, 70, 201, 191))


# 定义一个 Ui_MainWindow 类，用于设置主窗口的 UI



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(962, 699)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)



        self.num_drag = 0  # 记录拖拽作图次数的变量
        self.ResultFigures = {}
        self.ResultFigures[self.num_drag] = ResultFigure(MainWindow,"initical")
        self.ResultFigures[self.num_drag].MplCanvas = MplCanvas(self, width=5, height=5, dpi=100)
        self.ResultFigures[self.num_drag].MplCanvas.setGeometry(QRect(0, 0, 0, 0))



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
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Active, QPalette.PlaceholderText, brush5)
#endif
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
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush5)
#endif
        palette.setBrush(QPalette.Inactive, QPalette.Accent, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.WindowText, brush2)
        palette.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Light, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Midlight, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Dark, brush2)
        palette.setBrush(QPalette.Disabled, QPalette.Mid, brush3)
        palette.setBrush(QPalette.Disabled, QPalette.Text, brush2)
        palette.setBrush(QPalette.Disabled, QPalette.BrightText, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.ButtonText, brush2)
        palette.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.Shadow, brush)
        palette.setBrush(QPalette.Disabled, QPalette.AlternateBase, brush1)
        palette.setBrush(QPalette.Disabled, QPalette.ToolTipBase, brush4)
        palette.setBrush(QPalette.Disabled, QPalette.ToolTipText, brush)
        brush6 = QBrush(QColor(127, 127, 127, 127))
        brush6.setStyle(Qt.SolidPattern)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush6)
#endif
        palette.setBrush(QPalette.Disabled, QPalette.Accent, brush1)



        MainWindow.setPalette(palette)
        font = QFont()
        font.setPointSize(13)
        MainWindow.setFont(font)
        MainWindow.setWindowOpacity(1.000000000000000)
        MainWindow.setStyleSheet(u"background=rgb(255, 255, 255)")
        MainWindow.setIconSize(QSize(24, 24))
        MainWindow.setAnimated(True)
        MainWindow.setTabShape(QTabWidget.TabShape.Rounded)
        self.actionxinjian = QAction(MainWindow)
        self.actionxinjian.setObjectName(u"actionxinjian")
        self.actiondakai = QAction(MainWindow)
        self.actiondakai.setObjectName(u"actiondakai")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet(u"background = #ffffff")



        self.verticalLayoutWidget = QWidget(self.centralwidget)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(0, 0, 201, 651))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.toolBox = QToolBox(self.verticalLayoutWidget)
        self.toolBox.setObjectName(u"toolBox")
        self.toolBox.setMinimumSize(QSize(0, 649))
        self.toolBox.setBaseSize(QSize(0, 100))
        palette1 = QPalette()
        self.toolBox.setPalette(palette1)
        font1 = QFont()
        font1.setPointSize(14)
        font1.setBold(False)
        font1.setKerning(True)
        self.toolBox.setFont(font1)
        self.toolBox.setStyleSheet(u"background = rgb(255, 255, 255)")
        self.toolBox.setFrameShadow(QFrame.Shadow.Raised)
        self.toolBox.setLineWidth(0)
        self.toolBox.setMidLineWidth(0)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.page.setGeometry(QRect(0, 0, 199, 550))
        self.page.setSizeIncrement(QSize(0, 3))
        self.page.setStyleSheet(u"background = #ffffff")
        self.toolButton = QToolButton(self.page)
        self.toolButton.setObjectName(u"toolButton")
        self.toolButton.setGeometry(QRect(-10, -10, 211, 191))
        palette2 = QPalette()
        self.toolButton.setPalette(palette2)
        self.toolButton.setStyleSheet(u"color = rgb(255, 255, 255)\n"
"")
        self.toolBox.addItem(self.page, u"\u529f\u80fd1LocalBivariate")
        self.page_2 = QWidget()
        self.page_2.setObjectName(u"page_2")
        self.page_2.setGeometry(QRect(0, 0, 199, 550))
        self.toolBox.addItem(self.page_2, u"\u7559\u5f85\u529f\u80fd2")
        self.widget = QWidget()
        self.widget.setObjectName(u"widget")
        self.toolBox.addItem(self.widget, u"\u7559\u5f85\u529f\u80fd3")
        self.verticalLayout.addWidget(self.toolBox)



        self.widget_2 = QWidget(self.centralwidget)
        self.widget_2.setObjectName(u"widget_2")
        self.widget_2.setGeometry(QRect(200, 0, 900, 600))

        self.tabWidget = custom_tabWidget(self.widget_2)
        self.tabWidget.setStyleSheet(u"background = rgb(255, 255, 255)")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")



        palette3 = QPalette()
        palette3.setBrush(QPalette.Active, QPalette.WindowText, brush)
        palette3.setBrush(QPalette.Active, QPalette.Button, brush1)
        palette3.setBrush(QPalette.Active, QPalette.Light, brush1)
        palette3.setBrush(QPalette.Active, QPalette.Midlight, brush1)
        palette3.setBrush(QPalette.Active, QPalette.Dark, brush2)
        palette3.setBrush(QPalette.Active, QPalette.Mid, brush3)
        palette3.setBrush(QPalette.Active, QPalette.Text, brush)
        palette3.setBrush(QPalette.Active, QPalette.BrightText, brush1)
        palette3.setBrush(QPalette.Active, QPalette.ButtonText, brush)
        palette3.setBrush(QPalette.Active, QPalette.Base, brush1)
        palette3.setBrush(QPalette.Active, QPalette.Window, brush1)
        palette3.setBrush(QPalette.Active, QPalette.Shadow, brush)
        palette3.setBrush(QPalette.Active, QPalette.AlternateBase, brush1)
        palette3.setBrush(QPalette.Active, QPalette.ToolTipBase, brush4)
        palette3.setBrush(QPalette.Active, QPalette.ToolTipText, brush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette3.setBrush(QPalette.Active, QPalette.PlaceholderText, brush5)
#endif
        palette3.setBrush(QPalette.Active, QPalette.Accent, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        palette3.setBrush(QPalette.Inactive, QPalette.Button, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.Light, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.Midlight, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.Dark, brush2)
        palette3.setBrush(QPalette.Inactive, QPalette.Mid, brush3)
        palette3.setBrush(QPalette.Inactive, QPalette.Text, brush)
        palette3.setBrush(QPalette.Inactive, QPalette.BrightText, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.ButtonText, brush)
        palette3.setBrush(QPalette.Inactive, QPalette.Base, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.Window, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.Shadow, brush)
        palette3.setBrush(QPalette.Inactive, QPalette.AlternateBase, brush1)
        palette3.setBrush(QPalette.Inactive, QPalette.ToolTipBase, brush4)
        palette3.setBrush(QPalette.Inactive, QPalette.ToolTipText, brush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette3.setBrush(QPalette.Inactive, QPalette.PlaceholderText, brush5)
#endif
        palette3.setBrush(QPalette.Inactive, QPalette.Accent, brush1)
        palette3.setBrush(QPalette.Disabled, QPalette.WindowText, brush2)
        palette3.setBrush(QPalette.Disabled, QPalette.Button, brush1)
        palette3.setBrush(QPalette.Disabled, QPalette.Light, brush1)
        palette3.setBrush(QPalette.Disabled, QPalette.Midlight, brush1)
        palette3.setBrush(QPalette.Disabled, QPalette.Dark, brush2)
        palette3.setBrush(QPalette.Disabled, QPalette.Mid, brush3)
        palette3.setBrush(QPalette.Disabled, QPalette.Text, brush2)
        palette3.setBrush(QPalette.Disabled, QPalette.BrightText, brush1)
        palette3.setBrush(QPalette.Disabled, QPalette.ButtonText, brush2)
        palette3.setBrush(QPalette.Disabled, QPalette.Base, brush1)
        palette3.setBrush(QPalette.Disabled, QPalette.Window, brush1)
        palette3.setBrush(QPalette.Disabled, QPalette.Shadow, brush)
        palette3.setBrush(QPalette.Disabled, QPalette.AlternateBase, brush1)
        palette3.setBrush(QPalette.Disabled, QPalette.ToolTipBase, brush4)
        palette3.setBrush(QPalette.Disabled, QPalette.ToolTipText, brush)
#if QT_VERSION >= QT_VERSION_CHECK(5, 12, 0)
        palette3.setBrush(QPalette.Disabled, QPalette.PlaceholderText, brush6)
#endif
        palette3.setBrush(QPalette.Disabled, QPalette.Accent, brush1)


        self.tab.setPalette(palette3)
        self.tabWidget.setMouseTracking(True)
        layout = QVBoxLayout(self.widget_2)
        self.tabWidget.setGeometry(QRect(199, 111, 500, 600))
        layout.addWidget(self.tabWidget)
        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 962, 33))
        self.menu = QMenu(self.menubar)
        self.menu.setObjectName(u"menu")
        self.menu_2 = QMenu(self.menubar)
        self.menu_2.setObjectName(u"menu_2")
        self.menu_3 = QMenu(self.menubar)
        self.menu_3.setObjectName(u"menu_3")
        self.menu_4 = QMenu(self.menubar)
        self.menu_4.setObjectName(u"menu_4")
        self.menus = QMenu(self.menubar)
        self.menus.setObjectName(u"menus")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())
        self.menubar.addAction(self.menu_3.menuAction())
        self.menubar.addAction(self.menu_4.menuAction())
        self.menubar.addAction(self.menus.menuAction())
        self.menu.addAction(self.actionxinjian)
        self.menu.addAction(self.actiondakai)

        self.retranslateUi(MainWindow)

        self.toolBox.setCurrentIndex(0)
        self.toolBox.layout().setSpacing(0)
        self.tabWidget.setCurrentIndex(0)

        # Add a method to add a new tab with a plot



        QMetaObject.connectSlotsByName(MainWindow)


    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.actionxinjian.setText(QCoreApplication.translate("MainWindow", u"\u65b0\u5efa", None))
        self.actiondakai.setText(QCoreApplication.translate("MainWindow", u"\u6253\u5f00", None))
        self.toolButton.setText(QCoreApplication.translate("MainWindow", u"\u672c\u5730\u8ba1\u7b97", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page), QCoreApplication.translate("MainWindow", u"\u529f\u80fd1LocalBivariate", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), QCoreApplication.translate("MainWindow", u"\u7559\u5f85\u529f\u80fd2", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.widget), QCoreApplication.translate("MainWindow", u"\u7559\u5f85\u529f\u80fd3", None))
        self.menu.setTitle(QCoreApplication.translate("MainWindow", u"\u6587\u4ef6", None))
        self.menu_2.setTitle(QCoreApplication.translate("MainWindow", u"\u7f16\u8f91", None))
        self.menu_3.setTitle(QCoreApplication.translate("MainWindow", u"\u89c6\u56fe", None))
        self.menu_4.setTitle(QCoreApplication.translate("MainWindow", u"\u5e2e\u52a9", None))
        self.menus.setTitle(QCoreApplication.translate("MainWindow", u"\u8bbe\u7f6e ", None))
        #self.tab_2.setTitle(QCoreApplication.translate("MainWindow", u"\u56fe\u50cf\u5c5e\u6027\u914d\u7f6e", None))
    # retranslateUi
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()