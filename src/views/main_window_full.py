# Backup of main_window_full.py before MiniPlot simplification
# -*- coding: utf-8 -*-
"""
主窗口 - 完整功能版

从旧版本迁移：spr_gui_main.py - MainWindow
集成所有新组件：树形导航、数据表格、绘图画布等
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QToolBar, QTabWidget, QSizePolicy, QLabel, QStackedLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon
try:
    from qfluentwidgets import FluentIcon
except ImportError:
    FluentIcon = None
import config
from .widgets import (
    ProjectTreeWidget,
    DataTableWidget,
    ResultTableWidget,
    ProjectDetailTableWidget,
    CanvasWidget,
    SeriesTreeWidget
)
# ⭐ 导入新的Canvas实现（直接继承FigureCanvas）
# 使用具备滚轮缩放/平移/双击复位与视图持久化的CanvasWidget
# from .widgets.canvas_widget_new import CanvasWidgetWithToolbar
from .widgets.main_area_drop import MainAreaDropFilter
from .widgets.canvas_pg import PgCanvasWidget


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
        
        # 中间面板作为中央区域
        center_panel = self._create_center_panel()
        main_layout.addWidget(center_panel)
        # 左侧Dock（数据/系列）默认创建，右侧Dock按需
        self._create_left_docks()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        # 会话名称标签（置于状态栏左侧）
        self.session_label = QLabel()
        self.statusBar().addWidget(self.session_label)
        self.set_session_name("未命名会话")
        
        # 应用样式
        self._apply_styles()
    
    def _create_menubar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        new_action = QAction("新建会话(&N)", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("新建一个空白会话")
        file_menu.addAction(new_action)
        
        # 导入数据（JSON/Excel等原始数据文件）
        import_action = QAction("导入数据(&I)", self)
        import_action.setStatusTip("导入JSON/Excel/CSV等数据文件")
        file_menu.addAction(import_action)
        
        # 打开会话（.sprx）
        open_session_action = QAction("打开会话(&O)", self)
        open_session_action.setShortcut("Ctrl+O")
        open_session_action.setStatusTip("打开.sprx会话文件")
        file_menu.addAction(open_session_action)
        
        save_action = QAction("保存(&S)", self)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为(&A)", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setStatusTip("将当前会话另存为.sprx")
        file_menu.addAction(save_as_action)
        
        rename_session_action = QAction("重命名会话(&R)...", self)
        rename_session_action.setStatusTip("设置当前会话名称")
        file_menu.addAction(rename_session_action)

        # 最近打开
        recent_menu = file_menu.addMenu("最近打开")
        # 初始空，交由Controller填充

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
        
        # 自动保存控制
        auto_save_toggle = QAction("自动保存", self)
        auto_save_toggle.setCheckable(True)
        tools_menu.addAction(auto_save_toggle)

        auto_save_interval = QAction("设置自动保存间隔...", self)
        tools_menu.addAction(auto_save_interval)

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
        self.menu_new_action = new_action
        self.menu_import_data_action = import_action
        self.menu_open_session_action = open_session_action
        self.menu_save_action = save_action
        self.menu_save_as_action = save_as_action
        self.menu_rename_session_action = rename_session_action
        self.recent_menu = recent_menu
        self.stats_action = stats_action
        self.links_action = links_action
        self.clear_action = clear_action
        self.export_graph_action = export_graph_action
        self.test_guide_action = test_guide_action
        self.auto_save_toggle_action = auto_save_toggle
        self.auto_save_interval_action = auto_save_interval
    
    def _create_toolbar(self):
        """创建工具栏（现代化、简洁）"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # 导入数据
        import_action = QAction("导入", self)
        import_action.setStatusTip("导入JSON/Excel/CSV等数据文件")
        toolbar.addAction(import_action)
        
        # 打开会话
        open_action = QAction("打开会话", self)
        open_action.setStatusTip("打开.sprx会话文件")
        toolbar.addAction(open_action)
        
        # 保存
        save_action = QAction("保存", self)
        toolbar.addAction(save_action)
        
        # 另存为（工具栏可选占位）
        save_as_action = QAction("另存为", self)
        toolbar.addAction(save_as_action)
        
        toolbar.addSeparator()
        
        # 拟合
        fit_action = QAction("拟合", self)
        fit_action.setStatusTip("开始数据拟合")
        toolbar.addAction(fit_action)
        # 暴露给Controller连接（工具栏按钮）
        self.toolbar_fit_action = fit_action
        self.toolbar_import_action = import_action
        self.toolbar_open_session_action = open_action
        self.toolbar_save_action = save_action
        self.toolbar_save_as_action = save_as_action
        
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
    
    def _create_left_docks(self):
        """创建左侧可停靠面板（项目树/系列树）"""
        from PySide6.QtWidgets import QDockWidget
        # 项目导航树 Dock
        self.project_tree = ProjectTreeWidget()
        self.data_dock = QDockWidget("数据", self)
        self.data_dock.setWidget(self.project_tree)
        self.data_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.data_dock)

        # 系列树 Dock
        self.series_tree = SeriesTreeWidget()
        self.series_dock = QDockWidget("系列", self)
        self.series_dock.setWidget(self.series_tree)
        self.series_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.series_dock)

        # 垂直分布（上：数据树，下：系列树）
        try:
            self.splitDockWidget(self.data_dock, self.series_dock, Qt.Vertical)
        except Exception:
            pass
    
    def _create_center_panel(self) -> QWidget:
        """创建中间面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()

        # Tab 0: 数据表格（在本页内提供拖拽提示区域）
        self.data_tab = QWidget()
        # 使用叠放布局：将提示覆盖在数据表格上方，首次导入后隐藏
        data_stack = QStackedLayout(self.data_tab)
        data_stack.setStackingMode(QStackedLayout.StackAll)
        # 底层：数据表格
        self.data_table = DataTableWidget()
        data_stack.addWidget(self.data_table)
        # 顶层：拖拽提示覆盖层
        self.data_overlay = QWidget()
        overlay_layout = QVBoxLayout(self.data_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        self.data_drop_hint_label = QLabel("将文件拖到此页以导入数据（或通过 文件→导入数据）")
        self.data_drop_hint_label.setAlignment(Qt.AlignCenter)
        self.data_drop_hint_label.setStyleSheet("color:#666; padding:12px; font-size:13px;")
        overlay_layout.addStretch(1)
        overlay_layout.addWidget(self.data_drop_hint_label)
        overlay_layout.addStretch(1)
        data_stack.addWidget(self.data_overlay)
        self.tab_widget.addTab(self.data_tab, "数据表格")
        
        # Tab 1: 图表显示（切换为基于pyqtgraph的高性能绘图控件）
        self.canvas_widget = PgCanvasWidget()
        # 提高伸展策略，确保画布获得更多空间
        self.canvas_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tab_widget.addTab(self.canvas_widget, "图表显示")
        
        # Tab 2: 拟合结果
        self.result_table = ResultTableWidget()
        self.tab_widget.addTab(self.result_table, "拟合结果")
        # Tab 3: 项目详情
        self.project_detail_table = ProjectDetailTableWidget()
        self.tab_widget.addTab(self.project_detail_table, "项目详情")

        layout.addWidget(self.tab_widget)

        # 主工作区拖放：为Tab安装过滤器
        try:
            self._drop_filter = MainAreaDropFilter(self)
            # 允许TabWidget与“数据表格”TAB及覆盖层接收拖拽
            self.tab_widget.setAcceptDrops(True)
            self.tab_widget.installEventFilter(self._drop_filter)
            self.data_tab.setAcceptDrops(True)
            self.data_tab.installEventFilter(self._drop_filter)
            self.data_overlay.setAcceptDrops(True)
            self.data_overlay.installEventFilter(self._drop_filter)
            # 也可让数据表格本体接收
            self.data_table.setAcceptDrops(True)
            self.data_table.installEventFilter(self._drop_filter)
        except Exception:
            pass
        
        return panel

    def _create_right_dock(self):
        """按需创建右侧Dock（默认不创建）"""
        from PySide6.QtWidgets import QDockWidget, QTabWidget
        self.right_tabs = QTabWidget()
        self.right_tabs.addTab(self.result_table, "拟合结果")
        self.right_tabs.addTab(self.project_detail_table, "项目详情")
        self.right_dock = QDockWidget("分析", self)
        self.right_dock.setWidget(self.right_tabs)
        self.right_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)
        # 默认不 addDockWidget，以后在浮出时动态调用 addDockWidget
    
    def _connect_signals(self):
        """连接内部信号"""
        # 项目树节点点击
        self.project_tree.item_clicked.connect(self.on_tree_item_clicked)

        # 拦截关闭事件：提示未保存
        self.installEventFilter(self)
    
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
        """统一走高性能绘图通道（PgCanvasWidget），自动切图表Tab"""
        self.tab_widget.setCurrentIndex(1)
        try:
            if hasattr(self.canvas_widget, 'plot_line'):
                self.canvas_widget.plot_line(x_data, y_data, label=label,
                                             color=kwargs.get('color', '#1a73e8'),
                                             linewidth=kwargs.get('linewidth', 2))
            else:
                # 兜底：旧Matplotlib通道
                ax = getattr(self.canvas_widget, 'axes', None)
                if ax is None:
                    print('[MiniPlot] 错误：找不到Axes')
                    return
                ax.cla()
                ax.plot(x_data, y_data, label=label, color=kwargs.get('color', '#1a73e8'), linewidth=kwargs.get('linewidth', 2))
                ax.legend(loc='best')
                ax.grid(True, alpha=0.3, linestyle='--')
                try:
                    self.canvas_widget.canvas_widget.draw()
                except Exception:
                    self.canvas_widget.draw()
        except Exception as e:
            print('[MiniPlot] 绘制异常:', e)
            return
    
    
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

    def set_session_name(self, name: str):
        """设置状态栏的会话名称显示"""
        if hasattr(self, 'session_label') and self.session_label is not None:
            self.session_label.setText(f"会话: {name}")

    # ========== 事件过滤（关闭拦截） ==========
    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Close:
            # 若控制器提供关闭前处理，则调用
            controller = getattr(self, 'controller', None)
            if controller and hasattr(controller, 'try_handle_close'):
                allow = controller.try_handle_close()
                if not allow:
                    event.ignore()
                    return True
        return super().eventFilter(obj, event)

