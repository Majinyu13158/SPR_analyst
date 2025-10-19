import sys
from model_data_process.LocalBivariate import model_runner
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,Signal,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QMainWindow,
    QMenu, QMenuBar, QSizePolicy, QStatusBar,
    QTabWidget, QToolBox, QToolButton, QVBoxLayout,
    QWidget,QFileDialog)
class DraggableLabel(QLabel):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setAcceptDrops(True)
        self.isMousePressing = False
        self.mousePressPosition = None

        print(f"Parent object name: {parent.objectName()}")

    # 鼠标按下事件处理
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.isMousePressing = True
            self.mousePressPosition = event.globalPosition().toPoint()
            file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "",
                                                       "All Files (*);;Text Files (*.txt);;Image Files (*.png *.jpg *.gif);;*.xlsx")

            # 如果用户选择了文件，打印出文件路径
            if file_path:
                print(f"选中的文件路径: {file_path}")
        elif event.button() == Qt.RightButton:
            self.LabelStateChangeed()

    # 鼠标移动事件处理
    def mouseMoveEvent(self, event):
        if self.isMousePressing:
            movePosition = event.globalPosition().toPoint() - self.mousePressPosition
            self.mousePressPosition = event.globalPosition().toPoint()

    # 鼠标释放事件处理
    def mouseReleaseEvent(self, event):
        self.isMousePressing = False

    def LabelStateChangeed(self):
        print("label back changed")
        palette = QPalette()
        palette.setColor(QPalette.WindowText, QColor("red"))
        self.setPalette(palette)
        self.titleLabel = QLabel("已拖拽", self)

    # 拖拽进入事件处理
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

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
        window.ResultFigures[window.num_drag].MplCanvas.axes.scatter(T_data, Y_data, color='blue', label='Data')
        window.ResultFigures[window.num_drag].MplCanvas.axes.plot(T_data, Y_pred, color='red', label='Fit')
        window.ResultFigures[window.num_drag].MplCanvas.axes.legend(['Data', 'Fit'])
        window.ResultFigures[window.num_drag].MplCanvas.lower()
        current_tab = window.tabWidget.currentWidget()
        print(current_tab.objectName())
        layout = current_tab.layout()
        if layout is None:
            layout = QVBoxLayout(current_tab)
            current_tab.setLayout(layout)
            print("layout created")
            midwidget = QWidget(current_tab)
        layout.addWidget(midwidget)
        midwidget.setLayout(QVBoxLayout())
        midwidget.layout().addWidget(window.ResultFigures[window.num_drag].MplCanvas)
        layout.addWidget(window.ResultFigures[window.num_drag].MplCanvas)
        window.ResultFigures[window.num_drag].MplCanvas.resize(300,100)
        #window.centralwidget.layout().removeWidget(window.ResultFigures[window.num_drag-1].MplCanvas)
        #window.centralwidget.layout().addWidget(window.ResultFigures[window.num_drag].MplCanvas)

        current_text = window.label_4.text()
        new_text = current_text + window.ResultFigures[window.num_drag].name + '(' + str(window.num_drag) + ")" + '\n'
        window.label_4.setText(new_text)
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.DraggableLabel = DraggableLabel("拖拽作图", self.centralwidget)
        layout = QVBoxLayout(self.centralwidget)
        layout.addWidget(self.DraggableLabel)
        self.centralwidget.setLayout(layout)
        MainWindow.setCentralWidget(self.centralwidget)

        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
    # retranslateUi

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()

#main文件,三个文件，一个放drag，一个放tab，ui独自站一个
#main先跑一下创建出一个window，然后把这个window穿到drag那里
