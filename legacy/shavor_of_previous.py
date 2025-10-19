self.num_drag = 0  # 记录拖拽作图次数的变量
        self.ResultFigures = {}
        self.ResultFigures[self.num_drag] = ResultFigure(MainWindow,"initical")
        self.ResultFigures[self.num_drag].MplCanvas = MplCanvas(self, width=5, height=5, dpi=100)
        self.ResultFigures[self.num_drag].MplCanvas.setGeometry(QRect(0, 0, 0, 0))

class ResultFigure():
    def __init__(self,parent, name):
        self.MplCanvas = MplCanvas(parent, width=7, height=5, dpi=100)
        #self.toolbar = NavigationToolbar(self.MplCanvas, parent)
        self.name = name