# -*- coding: utf-8 -*-
"""
SPR传感器数据分析系统 - 简化完整版

使用标准PySide6组件，避免qfluentwidgets兼容性问题
"""
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QFileDialog, QMessageBox,
    QHeaderView, QMenuBar, QStatusBar
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
import pandas as pd

from src.models import DataManager, FigureManager, ResultManager
from src.utils import load_file
from src.views.widgets.canvas_widget import CanvasWidget
import config


class SimpleDragLabel(QLabel):
    """简化的拖拽标签"""
    file_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__("📁 拖拽文件到这里\n或点击选择文件", parent)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setMinimumHeight(80)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #1a73e8;
                border-radius: 8px;
                background: #f0f7ff;
                font-size: 14px;
                color: #1a73e8;
                padding: 20px;
            }
            QLabel:hover {
                background: #e3f2fd;
                border-color: #0d47a1;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "",
                "所有支持的文件 (*.json *.xlsx);;JSON Files (*.json);;Excel Files (*.xlsx)"
            )
            if file_path:
                self.file_selected.emit(file_path)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_selected.emit(files[0])


class SimpleMainWindow(QMainWindow):
    """简化的主窗口 - 使用标准PySide6组件"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.WINDOW_TITLE + " - 简化版")
        self.resize(1200, 800)
        
        # Model层
        self.data_manager = DataManager()
        self.figure_manager = FigureManager()
        self.result_manager = ResultManager()
        
        # 当前选中
        self.current_data_id = None
        
        # 创建UI
        self._setup_ui()
        self._connect_signals()
        
        self.statusBar().showMessage("就绪")
    
    def _setup_ui(self):
        """设置UI"""
        # 菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件(&F)")
        
        open_action = QAction("打开(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.on_open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        exit_action = QAction("退出(&X)", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 分析菜单
        analysis_menu = menubar.addMenu("分析(&A)")
        fit_action = QAction("开始拟合(&F)", self)
        fit_action.setShortcut("F5")
        fit_action.triggered.connect(self.on_start_fitting)
        analysis_menu.addAction(fit_action)
        
        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
    
    def _create_left_panel(self):
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 拖拽区
        self.drag_label = SimpleDragLabel()
        layout.addWidget(self.drag_label)
        
        # 标题
        title = QLabel("项目导航")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 树形控件
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        
        # 根节点
        self.data_root = QTreeWidgetItem(["📁 数据"])
        self.tree.addTopLevelItem(self.data_root)
        self.data_root.setExpanded(True)
        
        self.figure_root = QTreeWidgetItem(["📊 图表"])
        self.tree.addTopLevelItem(self.figure_root)
        
        self.result_root = QTreeWidgetItem(["✓ 结果"])
        self.tree.addTopLevelItem(self.result_root)
        
        layout.addWidget(self.tree)
        
        return panel
    
    def _create_right_panel(self):
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 选项卡
        self.tabs = QTabWidget()
        
        # Tab 1: 数据表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels(["ID", "时间", "X值", "Y值", "Y预测"])
        self.data_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.data_table, "📋 数据表格")
        
        # Tab 2: 图表
        self.canvas = CanvasWidget(dpi=100)
        self.tabs.addTab(self.canvas, "📈 图表显示")
        
        # Tab 3: 结果
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["参数", "值", "误差", "单位"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.result_table, "✓ 拟合结果")
        
        layout.addWidget(self.tabs)
        
        return panel
    
    def _connect_signals(self):
        """连接信号"""
        self.drag_label.file_selected.connect(self.on_file_selected)
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        self.data_manager.data_added.connect(self.on_data_added)
    
    @Slot(str)
    def on_file_selected(self, file_path: str):
        """文件选择"""
        self.statusBar().showMessage(f"正在加载: {file_path}")
        
        success, df, error = load_file(file_path)
        
        if not success:
            QMessageBox.critical(self, "加载失败", error)
            self.statusBar().showMessage("加载失败")
            return
        
        import os
        file_name = os.path.basename(file_path)
        data_id = self.data_manager.add_data(file_name, df)
        
        self.statusBar().showMessage(f"已加载: {file_name}")
    
    @Slot(int)
    def on_data_added(self, data_id: int):
        """数据添加后"""
        data = self.data_manager.get_data(data_id)
        if data:
            item = QTreeWidgetItem(self.data_root, [f"📄 {data.name}"])
            item.setData(0, Qt.UserRole, ('data', data_id))
    
    @Slot(object, int)
    def on_tree_item_clicked(self, item, column):
        """树节点点击"""
        data = item.data(0, Qt.UserRole)
        if data and data[0] == 'data':
            data_id = data[1]
            self.current_data_id = data_id
            self.show_data(data_id)
    
    def show_data(self, data_id: int):
        """显示数据"""
        data = self.data_manager.get_data(data_id)
        if not data or data.dataframe is None:
            return
        
        df = data.dataframe
        
        # 显示表格
        self.data_table.setRowCount(len(df))
        for row_idx, (_, row) in enumerate(df.iterrows()):
            for col_idx, col_name in enumerate(['ID', 'XValue', 'YValue']):
                if col_name in df.columns:
                    item = QTableWidgetItem(str(row[col_name]))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.data_table.setItem(row_idx, col_idx, item)
        
        # 绘图
        try:
            x_data, y_data = data.get_xy_data()
            self.canvas.plot_line(x_data, y_data, label=data.name)
            self.tabs.setCurrentIndex(1)
        except Exception as e:
            self.statusBar().showMessage(f"绘图失败: {str(e)}")
    
    def on_open_file(self):
        """打开文件菜单"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "",
            "所有支持的文件 (*.json *.xlsx);;JSON Files (*.json);;Excel Files (*.xlsx)"
        )
        if file_path:
            self.on_file_selected(file_path)
    
    def on_start_fitting(self):
        """开始拟合"""
        if self.current_data_id is None:
            QMessageBox.warning(self, "提示", "请先选择数据！")
            return
        
        QMessageBox.information(
            self, "拟合功能", 
            "拟合功能正在开发中...\n\n当前选中数据ID: {}".format(self.current_data_id)
        )


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SimpleMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

