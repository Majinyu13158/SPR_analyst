# -*- coding: utf-8 -*-
"""
主窗口 - MVP简化版
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QTextEdit, QTabWidget, QSplitter
)
from PySide6.QtCore import Qt, Signal
import config
from .widgets.draggable_label import DraggableLabel


class MainWindow(QMainWindow):
    """
    主窗口类 - MVP简化版
    
    信号:
        file_selected: 文件被选择，参数(文件路径)
    """
    file_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 窗口基本设置
        self.setWindowTitle(config.WINDOW_TITLE + " - MVP")
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - 项目列表
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板 - 主工作区
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        
        # 应用样式
        self._apply_styles()
    
    def _create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title = QLabel("数据列表")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 数据列表容器
        self.data_list_widget = QTextEdit()
        self.data_list_widget.setReadOnly(True)
        self.data_list_widget.setPlaceholderText("暂无数据\n\n请在右侧拖拽或选择文件")
        layout.addWidget(self.data_list_widget)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 欢迎页
        welcome_tab = QWidget()
        welcome_layout = QVBoxLayout(welcome_tab)
        
        welcome_label = QLabel("欢迎使用 SPR Sensor Analyst")
        welcome_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        
        # 拖拽区域
        self.drag_label = DraggableLabel()
        self.drag_label.file_selected.connect(self.on_file_selected)
        welcome_layout.addWidget(self.drag_label)
        
        info_label = QLabel(
            "MVP版本功能:\n"
            "• 支持拖拽或选择JSON/Excel文件\n"
            "• 显示数据列表\n"
            "• 基本的MVC架构演示"
        )
        info_label.setStyleSheet("color: #666; padding: 20px;")
        info_label.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(info_label)
        
        self.tab_widget.addTab(welcome_tab, "欢迎")
        
        # 数据详情页（占位）
        self.data_tab = QWidget()
        data_layout = QVBoxLayout(self.data_tab)
        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        self.data_display.setPlaceholderText("选择文件后，数据将显示在这里...")
        data_layout.addWidget(self.data_display)
        self.tab_widget.addTab(self.data_tab, "数据详情")
        
        layout.addWidget(self.tab_widget)
        
        return panel
    
    def on_file_selected(self, file_path: str):
        """处理文件选择事件"""
        # 发射信号给Controller
        self.file_selected.emit(file_path)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                font-family: 'Microsoft YaHei', Arial;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
                background: #e0e0e0;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #1a73e8;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                background: white;
            }
        """)
    
    # ========== 公共接口方法 ==========
    # Controller调用这些方法更新View
    
    def add_data_to_list(self, data_id: int, data_name: str):
        """添加数据到列表"""
        current_text = self.data_list_widget.toPlainText()
        if current_text == "暂无数据\n\n请在右侧拖拽或选择文件":
            current_text = ""
        
        new_text = f"{current_text}\n[{data_id}] {data_name}"
        self.data_list_widget.setText(new_text.strip())
    
    def show_data_detail(self, data_info: str):
        """显示数据详情"""
        self.data_display.setText(data_info)
        self.tab_widget.setCurrentIndex(1)  # 切换到数据详情标签
    
    def show_message(self, title: str, message: str):
        """显示消息"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)
    
    def show_error(self, title: str, message: str):
        """显示错误消息"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, title, message)

