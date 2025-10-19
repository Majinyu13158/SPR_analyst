# -*- coding: utf-8 -*-
"""
设置对话框

从旧版本迁移：custom_widgets/custom_Dialog_for_MplCanvas_Attribtes_Change.py
功能：图表属性设置
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QPushButton, QLabel, QTabWidget, QWidget, QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor


class SettingsDialog(QDialog):
    """
    设置对话框
    
    功能：
        - 图表属性设置
        - 绘图样式设置
        - 应用程序设置
    
    信号：
        settings_changed: 设置已修改 (settings_dict)
    """
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(500, 400)
        
        # 当前设置
        self.current_settings = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # Tab 1: 图表设置
        plot_tab = self._create_plot_settings_tab()
        self.tab_widget.addTab(plot_tab, "图表")
        
        # Tab 2: 样式设置
        style_tab = self._create_style_settings_tab()
        self.tab_widget.addTab(style_tab, "样式")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_button = QPushButton("应用")
        self.apply_button.clicked.connect(self.on_apply)
        button_layout.addWidget(self.apply_button)
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.on_ok)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def _create_plot_settings_tab(self) -> QWidget:
        """创建图表设置标签页"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 标题
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("SPR Sensor Data")
        layout.addRow("图表标题:", self.title_edit)
        
        # X轴标签
        self.xlabel_edit = QLineEdit()
        self.xlabel_edit.setPlaceholderText("Time (s)")
        layout.addRow("X轴标签:", self.xlabel_edit)
        
        # Y轴标签
        self.ylabel_edit = QLineEdit()
        self.ylabel_edit.setPlaceholderText("Response (RU)")
        layout.addRow("Y轴标签:", self.ylabel_edit)
        
        # 图例位置
        self.legend_combo = QComboBox()
        self.legend_combo.addItems(['best', 'upper right', 'upper left', 'lower right', 'lower left'])
        layout.addRow("图例位置:", self.legend_combo)
        
        # 网格
        self.grid_combo = QComboBox()
        self.grid_combo.addItems(['显示', '隐藏'])
        layout.addRow("网格:", self.grid_combo)
        
        layout.addStretch()
        
        return tab
    
    def _create_style_settings_tab(self) -> QWidget:
        """创建样式设置标签页"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # 线条颜色
        color_layout = QHBoxLayout()
        self.line_color = "#1a73e8"
        self.color_button = QPushButton("选择颜色")
        self.color_button.clicked.connect(self.on_select_color)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 20)
        self.color_preview.setStyleSheet(f"background-color: {self.line_color}; border: 1px solid #ccc;")
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        layout.addRow("线条颜色:", color_layout)
        
        # 线宽
        self.linewidth_spin = QDoubleSpinBox()
        self.linewidth_spin.setRange(0.5, 10.0)
        self.linewidth_spin.setValue(2.0)
        self.linewidth_spin.setSingleStep(0.5)
        layout.addRow("线宽:", self.linewidth_spin)
        
        # 标记样式
        self.marker_combo = QComboBox()
        self.marker_combo.addItems(['o', 's', '^', 'v', 'D', '*', '+', 'x', 'none'])
        layout.addRow("标记样式:", self.marker_combo)
        
        # 标记大小
        self.markersize_spin = QDoubleSpinBox()
        self.markersize_spin.setRange(0, 20)
        self.markersize_spin.setValue(4.0)
        self.markersize_spin.setSingleStep(1.0)
        layout.addRow("标记大小:", self.markersize_spin)
        
        layout.addStretch()
        
        return tab
    
    def on_select_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(QColor(self.line_color), self, "选择线条颜色")
        if color.isValid():
            self.line_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.line_color}; border: 1px solid #ccc;")
    
    def on_apply(self):
        """应用设置"""
        settings = self.get_settings()
        self.settings_changed.emit(settings)
    
    def on_ok(self):
        """确定"""
        self.on_apply()
        self.accept()
    
    def get_settings(self) -> dict:
        """获取当前设置"""
        return {
            'plot': {
                'title': self.title_edit.text() or "SPR Sensor Data",
                'xlabel': self.xlabel_edit.text() or "Time (s)",
                'ylabel': self.ylabel_edit.text() or "Response (RU)",
                'legend_loc': self.legend_combo.currentText(),
                'grid': self.grid_combo.currentText() == '显示'
            },
            'style': {
                'line_color': self.line_color,
                'linewidth': self.linewidth_spin.value(),
                'marker': self.marker_combo.currentText(),
                'markersize': self.markersize_spin.value()
            }
        }
    
    def set_settings(self, settings: dict):
        """设置值"""
        plot_settings = settings.get('plot', {})
        style_settings = settings.get('style', {})
        
        # 图表设置
        self.title_edit.setText(plot_settings.get('title', ''))
        self.xlabel_edit.setText(plot_settings.get('xlabel', ''))
        self.ylabel_edit.setText(plot_settings.get('ylabel', ''))
        
        legend_loc = plot_settings.get('legend_loc', 'best')
        index = self.legend_combo.findText(legend_loc)
        if index >= 0:
            self.legend_combo.setCurrentIndex(index)
        
        grid = plot_settings.get('grid', True)
        self.grid_combo.setCurrentIndex(0 if grid else 1)
        
        # 样式设置
        self.line_color = style_settings.get('line_color', '#1a73e8')
        self.color_preview.setStyleSheet(f"background-color: {self.line_color}; border: 1px solid #ccc;")
        
        self.linewidth_spin.setValue(style_settings.get('linewidth', 2.0))
        
        marker = style_settings.get('marker', 'o')
        index = self.marker_combo.findText(marker)
        if index >= 0:
            self.marker_combo.setCurrentIndex(index)
        
        self.markersize_spin.setValue(style_settings.get('markersize', 4.0))

