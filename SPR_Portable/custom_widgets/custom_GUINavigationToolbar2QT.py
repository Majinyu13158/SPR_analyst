#本文件旨在自定义以qt为后端的matplotlib的导航工具栏

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib

class CustomNavigationToolbar(NavigationToolbar):
    def __init__(self, canvas):
        self.setStyleSheet("""QToolBar{background:black}
                                      QLabel{font:11pt 'Consolas'}""")
        super(CustomNavigationToolbar, self).__init__(canvas)
        self.remove_toolitem(self._actions['save'])


