# Backup of main_window_full.py before MiniPlot simplification
# -*- coding: utf-8 -*-
"""
主窗口 - 完整功能版

从旧版本迁移：spr_gui_main.py - MainWindow
集成所有新组件：树形导航、数据表格、绘图画布等
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QToolBar, QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon
try:
    from qfluentwidgets import FluentIcon
except ImportError:
    FluentIcon = None
import config
from .widgets import (
    DraggableLabel,
    ProjectTreeWidget,
    DataTableWidget,
    ResultTableWidget,
    ProjectDetailTableWidget,
    CanvasWidget
)
# ⭐ 导入新的Canvas实现（直接继承FigureCanvas）
from .widgets.canvas_widget_new import CanvasWidgetWithToolbar


class MainWindowFull(QMainWindow):
    """
    主窗口类 - 完整功能版
    
    布局结构：
        - 顶部：菜单栏 + 工具栏
        - 主体：3列分割
            - 左侧：项目导航树 + 拖拽区
            - 中间：选项卡（数据表格/图表/结果/详情）
            - 右侧：（可选）属性面板
    
    信号：
        file_selected: 文件被选择 (file_path)
        data_item_selected: 数据项被选择 (data_id)
        figure_item_selected: 图表项被选择 (figure_id)
        result_item_selected: 结果项被选择 (result_id)
        fitting_requested: 请求拟合 (data_id, method)
    """
    
    # 信号定义
    file_selected = Signal(str)
    data_item_selected = Signal(int)
    figure_item_selected = Signal(int)
    result_item_selected = Signal(int)
    fitting_requested = Signal(int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置UI"""
        # 窗口基本设置
        self.setWindowTitle(config.WINDOW_TITLE)
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        
        # 创建菜单栏和工具栏
        self._create_menubar()
        self._create_toolbar()
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建3列分割器
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - 项目树
        left_panel = self._create_left_panel()
        self.splitter.addWidget(left_panel)
        
        # 中间面板 - 主工作区
        center_panel = self._create_center_panel()
        self.splitter.addWidget(center_panel)
        
        # 设置分割比例 (1:3)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(self.splitter)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 应用样式
        self._apply_styles()
    
    def _create_menubar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        open_action = QAction("打开文件(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("打开数据文件")
        file_menu.addAction(open_action)
        
        save_action = QAction("保存(&S)", self)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 分析菜单
        analysis_menu = menubar.addMenu("分析(&A)")
        
        fit_action = QAction("开始拟合(&F)", self)
        fit_action.setShortcut("F5")
        analysis_menu.addAction(fit_action)
        # 暴露给Controller连接
        self.fit_action = fit_action
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        zoom_in_action = QAction("放大(&I)", self)
        zoom_in_action.setShortcut("Ctrl++")
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("缩小(&O)", self)
        zoom_out_action.setShortcut("Ctrl+-")
        view_menu.addAction(zoom_out_action)
        
        # 工具菜单（调试和实用功能）
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 查看会话统计
        stats_action = QAction("📊 查看会话统计(&S)", self)
        stats_action.setShortcut("Ctrl+I")
        stats_action.setStatusTip("查看当前会话的统计信息")
        tools_menu.addAction(stats_action)
        
        # 查看链接信息
        links_action = QAction("🔗 查看所有链接(&L)", self)
        links_action.setStatusTip("查看所有对象之间的链接关系")
        tools_menu.addAction(links_action)
        
        tools_menu.addSeparator()
        
        # 清空所有数据
        clear_action = QAction("🗑️ 清空所有数据(&C)", self)
        clear_action.setStatusTip("清空当前会话中的所有数据")
        tools_menu.addAction(clear_action)
        
        # 导出链接图
        export_graph_action = QAction("📈 导出链接图(&G)", self)
        export_graph_action.setStatusTip("导出数据血缘图")
        tools_menu.addAction(export_graph_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 快速测试指南
        test_guide_action = QAction("🧪 快速测试指南(&T)", self)
        test_guide_action.setShortcut("F1")
        help_menu.addAction(test_guide_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("关于(&A)", self)
        help_menu.addAction(about_action)
        
        # 连接信号（保存引用以便Controller连接）
        self.stats_action = stats_action
        self.links_action = links_action
        self.clear_action = clear_action
        self.export_graph_action = export_graph_action
        self.test_guide_action = test_guide_action
    
    def _create_toolbar(self):
        """创建工具栏（现代化、简洁）"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 打开文件
        open_action = QAction("打开", self)
        open_action.setStatusTip("打开数据文件")
        toolbar.addAction(open_action)
        
        # 保存
        save_action = QAction("保存", self)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # 拟合
        fit_action = QAction("拟合", self)
        fit_action.setStatusTip("开始数据拟合")
        toolbar.addAction(fit_action)
        # 暴露给Controller连接（工具栏按钮）
        self.toolbar_fit_action = fit_action
        
        # 额外基础按键（占位）
        toolbar.addSeparator()
        refresh_action = QAction("刷新", self)
        export_action = QAction("导出", self)
        settings_action = QAction("设置", self)
        help_action = QAction("帮助", self)
        toolbar.addAction(refresh_action)
        toolbar.addAction(export_action)
        toolbar.addAction(settings_action)
        toolbar.addAction(help_action)
    
    def _create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 拖拽区域
        self.drag_label = DraggableLabel()
        layout.addWidget(self.drag_label)
        
        # 项目导航树
        self.project_tree = ProjectTreeWidget()
        layout.addWidget(self.project_tree)
        
        return panel
    
    def _create_center_panel(self) -> QWidget:
        """创建中间面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # Tab 1: 数据表格
        self.data_table = DataTableWidget()
        self.tab_widget.addTab(self.data_table, "数据表格")
        
        # Tab 2: 图表显示
        # ⭐ 使用新的Canvas实现（参考原项目，直接继承FigureCanvas）
        self.canvas_widget = CanvasWidgetWithToolbar(dpi=100)
        # 提高伸展策略，确保画布获得更多空间
        self.canvas_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tab_widget.addTab(self.canvas_widget, "图表显示")
        
        # Tab 3: 结果表格
        self.result_table = ResultTableWidget()
        self.tab_widget.addTab(self.result_table, "拟合结果")
        
        # Tab 4: 项目详情
        self.project_detail_table = ProjectDetailTableWidget()
        self.tab_widget.addTab(self.project_detail_table, "项目详情")
        
        layout.addWidget(self.tab_widget)
        
        return panel
    
    def _connect_signals(self):
        """连接内部信号"""
        # 文件拖拽
        self.drag_label.file_selected.connect(self.on_file_selected)
        
        # 项目树节点点击
        self.project_tree.item_clicked.connect(self.on_tree_item_clicked)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                font-family: 'Microsoft YaHei', 'SimHei', Arial;
            }
            QToolBar {
                background: white;
                border-bottom: 1px solid #ddd;
                padding: 4px;
            }
            QMenuBar {
                background: white;
                border-bottom: 1px solid #ddd;
            }
            QMenuBar::item:selected {
                background: #e8f0fe;
            }
            QStatusBar {
                background: #f5f5f5;
                border-top: 1px solid #ddd;
            }
        """)
    
    # ========== 槽函数 ==========
    
    def on_file_selected(self, file_path: str):
        """处理文件选择"""
        self.file_selected.emit(file_path)
        self.statusBar().showMessage(f"已选择文件: {file_path}")
    
    def on_tree_item_clicked(self, item_type: str, item_id: int):
        """处理树节点点击"""
        if item_type == 'data':
            self.data_item_selected.emit(item_id)
            self.tab_widget.setCurrentIndex(0)  # 切换到数据表格
        elif item_type == 'figure':
            self.figure_item_selected.emit(item_id)
            self.tab_widget.setCurrentIndex(1)  # 切换到图表
        elif item_type == 'result':
            self.result_item_selected.emit(item_id)
            self.tab_widget.setCurrentIndex(2)  # 切换到结果
    
    # ========== 公共接口 ==========
    # Controller调用这些方法更新View
    
    def add_data_to_tree(self, data_id: int, name: str):
        """添加数据到树"""
        self.project_tree.add_data_item(data_id, name)
    
    def add_figure_to_tree(self, figure_id: int, name: str):
        """添加图表到树"""
        self.project_tree.add_figure_item(figure_id, name)
    
    def add_result_to_tree(self, result_id: int, name: str):
        """添加结果到树"""
        self.project_tree.add_result_item(result_id, name)
    
    def show_data_table(self, data):
        """显示数据表格"""
        self.data_table.load_data(data)
        self.tab_widget.setCurrentIndex(0)
    
    def show_plot(self, x_data, y_data, label='Data', **kwargs):
        """极简绘图通道（MiniPlot）：直接拿Axes→cla→plot→draw"""
        # 1) 先切换到图表标签页，保证可见
        self.tab_widget.setCurrentIndex(1)

        # 2) 直接拿到底层Axes并清空
        try:
            ax = self.canvas_widget.canvas_widget.axes
        except Exception:
            # 兜底：若封装变化，尝试旧路径
            ax = getattr(self.canvas_widget, 'axes', None)
        if ax is None:
            print('[MiniPlot] 错误：找不到Axes')
            return
        ax.cla()

        # 3) 只画一条线（不加legend/title/grid/tight_layout）
        ax.plot(x_data, y_data, color='#1a73e8', linewidth=2)

        # 4) 强制重绘
        try:
            self.canvas_widget.canvas_widget.draw()
        except Exception:
            # 兜底：如果封装不同，直接调用自身draw
            self.canvas_widget.draw()

        print('[MiniPlot] 绘制完成')
    
    
    def show_fitting_plot(self, x_data, y_data, y_pred):
        """
        显示拟合图表
        
        ⭐ 使用新的Canvas实现，简单直接
        """
        # 绘图
        self.canvas_widget.plot_fitting(x_data, y_data, y_pred)
        
        # 切换到图表标签页
        self.tab_widget.setCurrentIndex(1)
        
        print(f"[MainWindowFull] ✅ 拟合图绘制完成，已切换到图表Tab")
    
    def show_result(self, result_dict: dict):
        """显示拟合结果"""
        self.result_table.load_result(result_dict)
        self.tab_widget.setCurrentIndex(2)
    
    def show_project_detail(self, details: dict):
        """显示项目详情"""
        self.project_detail_table.load_details(details)
        self.tab_widget.setCurrentIndex(3)
    
    def show_message(self, title: str, message: str):
        """显示消息"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)
    
    def show_error(self, title: str, message: str):
        """显示错误"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.statusBar().showMessage(message)
    
    def highlight_tree_item(self, item_type: str, item_id: int):
        """
        高亮并跳转到指定树节点
        
        参数:
            item_type: 节点类型（data/figure/result/project）
            item_id: 节点ID
        """
        self.project_tree.highlight_item(item_type, item_id)

