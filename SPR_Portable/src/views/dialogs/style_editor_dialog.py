"""
图表样式编辑器对话框

功能：
1. 可视化编辑线条样式（颜色、宽度、样式）
2. 可视化编辑标记样式（类型、大小、颜色）
3. 实时预览样式效果
4. 应用样式到图表
5. 样式模板管理
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QPushButton, QLabel, QSlider, QComboBox, QCheckBox,
    QColorDialog, QGroupBox, QGridLayout, QLineEdit, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
import pyqtgraph as pg
import numpy as np
from typing import Dict, Any


class PlotStyle:
    """图表样式配置"""
    def __init__(self):
        # 线条样式
        self.line_color = QColor(0, 120, 215)  # 蓝色
        self.line_width = 2
        self.line_style = 'solid'
        
        # 标记样式
        self.symbol = 'o'
        self.symbol_size = 8
        self.symbol_color = QColor(0, 120, 215)
        self.symbol_edge_color = QColor(255, 255, 255)
        self.symbol_edge_width = 1
        
        # 坐标轴
        self.xlabel = "X轴"
        self.ylabel = "Y轴"
        self.label_font_size = 12
        self.show_grid = True
        self.grid_alpha = 0.3
        
        # 图例
        self.show_legend = True
        
        # 背景
        self.bg_color = QColor(255, 255, 255)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'line_color': (self.line_color.red(), self.line_color.green(), self.line_color.blue()),
            'line_width': self.line_width,
            'line_style': self.line_style,
            'symbol': self.symbol,
            'symbol_size': self.symbol_size,
            'symbol_color': (self.symbol_color.red(), self.symbol_color.green(), self.symbol_color.blue()),
            'symbol_edge_color': (self.symbol_edge_color.red(), self.symbol_edge_color.green(), self.symbol_edge_color.blue()),
            'symbol_edge_width': self.symbol_edge_width,
            'xlabel': self.xlabel,
            'ylabel': self.ylabel,
            'label_font_size': self.label_font_size,
            'show_grid': self.show_grid,
            'grid_alpha': self.grid_alpha,
            'show_legend': self.show_legend,
            'bg_color': (self.bg_color.red(), self.bg_color.green(), self.bg_color.blue())
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'PlotStyle':
        """从字典创建"""
        style = PlotStyle()
        if 'line_color' in data:
            style.line_color = QColor(*data['line_color'])
        if 'line_width' in data:
            style.line_width = data['line_width']
        if 'line_style' in data:
            style.line_style = data['line_style']
        if 'symbol' in data:
            style.symbol = data['symbol']
        if 'symbol_size' in data:
            style.symbol_size = data['symbol_size']
        if 'symbol_color' in data:
            style.symbol_color = QColor(*data['symbol_color'])
        if 'symbol_edge_color' in data:
            style.symbol_edge_color = QColor(*data['symbol_edge_color'])
        if 'symbol_edge_width' in data:
            style.symbol_edge_width = data['symbol_edge_width']
        if 'xlabel' in data:
            style.xlabel = data['xlabel']
        if 'ylabel' in data:
            style.ylabel = data['ylabel']
        if 'label_font_size' in data:
            style.label_font_size = data['label_font_size']
        if 'show_grid' in data:
            style.show_grid = data['show_grid']
        if 'grid_alpha' in data:
            style.grid_alpha = data['grid_alpha']
        if 'show_legend' in data:
            style.show_legend = data['show_legend']
        if 'bg_color' in data:
            style.bg_color = QColor(*data['bg_color'])
        return style


class StyleEditorDialog(QDialog):
    """样式编辑器对话框"""
    
    # 信号：样式已应用
    style_applied = Signal(dict)
    
    def __init__(self, current_style: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        
        # 当前样式
        if current_style:
            self.style = PlotStyle.from_dict(current_style)
        else:
            self.style = PlotStyle()
        
        # 示例数据（用于预览）
        self.preview_x = np.linspace(0, 10, 50)
        self.preview_y = np.sin(self.preview_x) * np.exp(-self.preview_x/10) + 2
        
        self._setup_ui()
        self._update_preview()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("图表样式编辑器")
        self.resize(900, 600)
        
        layout = QHBoxLayout(self)
        
        # ========== 左侧：样式选项 ==========
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 选项卡
        tab_widget = QTabWidget()
        
        # Tab 1: 线条样式
        line_tab = self._create_line_tab()
        tab_widget.addTab(line_tab, "📊 线条")
        
        # Tab 2: 标记样式
        symbol_tab = self._create_symbol_tab()
        tab_widget.addTab(symbol_tab, "● 标记")
        
        # Tab 3: 坐标轴样式
        axis_tab = self._create_axis_tab()
        tab_widget.addTab(axis_tab, "📏 坐标轴")
        
        left_layout.addWidget(tab_widget)
        
        # 模板选择
        template_group = QGroupBox("样式模板")
        template_layout = QVBoxLayout(template_group)
        
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "默认", "科研论文", "演示文稿", "彩色对比"
        ])
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        template_layout.addWidget(self.template_combo)
        
        left_layout.addWidget(template_group)
        
        left_panel.setMaximumWidth(350)
        layout.addWidget(left_panel)
        
        # ========== 右侧：预览区域 ==========
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("实时预览")
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(preview_label)
        
        # 预览图表
        self.preview_plot = pg.PlotWidget()
        self.preview_plot.setBackground('w')
        right_layout.addWidget(self.preview_plot)
        
        layout.addWidget(right_panel)
        
        # ========== 底部按钮 ==========
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self._on_apply)
        button_layout.addWidget(apply_btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self._on_reset)
        button_layout.addWidget(reset_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # 将按钮布局添加到左侧面板底部
        left_layout.addLayout(button_layout)
    
    def _create_line_tab(self) -> QWidget:
        """创建线条样式选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 线条颜色
        color_group = QGroupBox("线条颜色")
        color_layout = QHBoxLayout(color_group)
        
        self.line_color_btn = QPushButton("")
        self.line_color_btn.setFixedSize(50, 30)
        self._update_color_button(self.line_color_btn, self.style.line_color)
        self.line_color_btn.clicked.connect(self._on_line_color_clicked)
        color_layout.addWidget(self.line_color_btn)
        
        self.line_color_label = QLabel(self.style.line_color.name())
        color_layout.addWidget(self.line_color_label)
        color_layout.addStretch()
        
        layout.addWidget(color_group)
        
        # 线条宽度
        width_group = QGroupBox("线条宽度")
        width_layout = QVBoxLayout(width_group)
        
        width_h_layout = QHBoxLayout()
        self.line_width_slider = QSlider(Qt.Horizontal)
        self.line_width_slider.setMinimum(1)
        self.line_width_slider.setMaximum(10)
        self.line_width_slider.setValue(self.style.line_width)
        self.line_width_slider.valueChanged.connect(self._on_line_width_changed)
        width_h_layout.addWidget(self.line_width_slider)
        
        self.line_width_label = QLabel(f"{self.style.line_width} px")
        self.line_width_label.setFixedWidth(50)
        width_h_layout.addWidget(self.line_width_label)
        
        width_layout.addLayout(width_h_layout)
        layout.addWidget(width_group)
        
        # 线条样式
        style_group = QGroupBox("线条样式")
        style_layout = QHBoxLayout(style_group)
        
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(["实线", "虚线", "点线", "点划线"])
        style_map = {'solid': 0, 'dash': 1, 'dot': 2, 'dashdot': 3}
        self.line_style_combo.setCurrentIndex(style_map.get(self.style.line_style, 0))
        self.line_style_combo.currentIndexChanged.connect(self._on_line_style_changed)
        style_layout.addWidget(self.line_style_combo)
        
        layout.addWidget(style_group)
        
        layout.addStretch()
        return widget
    
    def _create_symbol_tab(self) -> QWidget:
        """创建标记样式选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 标记类型
        type_group = QGroupBox("标记类型")
        type_layout = QHBoxLayout(type_group)
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["圆形 ●", "方形 ■", "三角形 ▲", "菱形 ◆", "十字 +", "叉号 ×", "星形 ★"])
        symbol_map = {'o': 0, 's': 1, 't': 2, 'd': 3, '+': 4, 'x': 5, 'star': 6}
        self.symbol_combo.setCurrentIndex(symbol_map.get(self.style.symbol, 0))
        self.symbol_combo.currentIndexChanged.connect(self._on_symbol_changed)
        type_layout.addWidget(self.symbol_combo)
        
        layout.addWidget(type_group)
        
        # 标记大小
        size_group = QGroupBox("标记大小")
        size_layout = QVBoxLayout(size_group)
        
        size_h_layout = QHBoxLayout()
        self.symbol_size_slider = QSlider(Qt.Horizontal)
        self.symbol_size_slider.setMinimum(3)
        self.symbol_size_slider.setMaximum(20)
        self.symbol_size_slider.setValue(self.style.symbol_size)
        self.symbol_size_slider.valueChanged.connect(self._on_symbol_size_changed)
        size_h_layout.addWidget(self.symbol_size_slider)
        
        self.symbol_size_label = QLabel(f"{self.style.symbol_size} px")
        self.symbol_size_label.setFixedWidth(50)
        size_h_layout.addWidget(self.symbol_size_label)
        
        size_layout.addLayout(size_h_layout)
        layout.addWidget(size_group)
        
        # 标记颜色
        color_group = QGroupBox("标记颜色")
        color_layout = QHBoxLayout(color_group)
        
        self.symbol_color_btn = QPushButton("")
        self.symbol_color_btn.setFixedSize(50, 30)
        self._update_color_button(self.symbol_color_btn, self.style.symbol_color)
        self.symbol_color_btn.clicked.connect(self._on_symbol_color_clicked)
        color_layout.addWidget(self.symbol_color_btn)
        
        self.symbol_color_label = QLabel(self.style.symbol_color.name())
        color_layout.addWidget(self.symbol_color_label)
        color_layout.addStretch()
        
        layout.addWidget(color_group)
        
        layout.addStretch()
        return widget
    
    def _create_axis_tab(self) -> QWidget:
        """创建坐标轴样式选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 坐标轴标签
        label_group = QGroupBox("坐标轴标签")
        label_layout = QGridLayout(label_group)
        
        label_layout.addWidget(QLabel("X轴:"), 0, 0)
        self.xlabel_edit = QLineEdit(self.style.xlabel)
        self.xlabel_edit.textChanged.connect(self._on_xlabel_changed)
        label_layout.addWidget(self.xlabel_edit, 0, 1)
        
        label_layout.addWidget(QLabel("Y轴:"), 1, 0)
        self.ylabel_edit = QLineEdit(self.style.ylabel)
        self.ylabel_edit.textChanged.connect(self._on_ylabel_changed)
        label_layout.addWidget(self.ylabel_edit, 1, 1)
        
        layout.addWidget(label_group)
        
        # 字体大小
        font_group = QGroupBox("字体大小")
        font_layout = QVBoxLayout(font_group)
        
        font_h_layout = QHBoxLayout()
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setMinimum(8)
        self.font_size_slider.setMaximum(24)
        self.font_size_slider.setValue(self.style.label_font_size)
        self.font_size_slider.valueChanged.connect(self._on_font_size_changed)
        font_h_layout.addWidget(self.font_size_slider)
        
        self.font_size_label = QLabel(f"{self.style.label_font_size} pt")
        self.font_size_label.setFixedWidth(50)
        font_h_layout.addWidget(self.font_size_label)
        
        font_layout.addLayout(font_h_layout)
        layout.addWidget(font_group)
        
        # 网格线
        grid_group = QGroupBox("网格线")
        grid_layout = QVBoxLayout(grid_group)
        
        self.grid_check = QCheckBox("显示网格")
        self.grid_check.setChecked(self.style.show_grid)
        self.grid_check.stateChanged.connect(self._on_grid_changed)
        grid_layout.addWidget(self.grid_check)
        
        layout.addWidget(grid_group)
        
        # 图例
        legend_group = QGroupBox("图例")
        legend_layout = QVBoxLayout(legend_group)
        
        self.legend_check = QCheckBox("显示图例")
        self.legend_check.setChecked(self.style.show_legend)
        self.legend_check.stateChanged.connect(self._on_legend_changed)
        legend_layout.addWidget(self.legend_check)
        
        layout.addWidget(legend_group)
        
        layout.addStretch()
        return widget
    
    def _update_color_button(self, button: QPushButton, color: QColor):
        """更新颜色按钮显示"""
        button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #999;")
    
    def _on_line_color_clicked(self):
        """线条颜色点击"""
        color = QColorDialog.getColor(self.style.line_color, self, "选择线条颜色")
        if color.isValid():
            self.style.line_color = color
            self._update_color_button(self.line_color_btn, color)
            self.line_color_label.setText(color.name())
            self._update_preview()
    
    def _on_line_width_changed(self, value: int):
        """线条宽度改变"""
        self.style.line_width = value
        self.line_width_label.setText(f"{value} px")
        self._update_preview()
    
    def _on_line_style_changed(self, index: int):
        """线条样式改变"""
        styles = ['solid', 'dash', 'dot', 'dashdot']
        self.style.line_style = styles[index]
        self._update_preview()
    
    def _on_symbol_changed(self, index: int):
        """标记类型改变"""
        symbols = ['o', 's', 't', 'd', '+', 'x', 'star']
        self.style.symbol = symbols[index]
        self._update_preview()
    
    def _on_symbol_size_changed(self, value: int):
        """标记大小改变"""
        self.style.symbol_size = value
        self.symbol_size_label.setText(f"{value} px")
        self._update_preview()
    
    def _on_symbol_color_clicked(self):
        """标记颜色点击"""
        color = QColorDialog.getColor(self.style.symbol_color, self, "选择标记颜色")
        if color.isValid():
            self.style.symbol_color = color
            self._update_color_button(self.symbol_color_btn, color)
            self.symbol_color_label.setText(color.name())
            self._update_preview()
    
    def _on_xlabel_changed(self, text: str):
        """X轴标签改变"""
        self.style.xlabel = text
        self._update_preview()
    
    def _on_ylabel_changed(self, text: str):
        """Y轴标签改变"""
        self.style.ylabel = text
        self._update_preview()
    
    def _on_font_size_changed(self, value: int):
        """字体大小改变"""
        self.style.label_font_size = value
        self.font_size_label.setText(f"{value} pt")
        self._update_preview()
    
    def _on_grid_changed(self, state: int):
        """网格显示改变"""
        self.style.show_grid = (state == Qt.Checked)
        self._update_preview()
    
    def _on_legend_changed(self, state: int):
        """图例显示改变"""
        self.style.show_legend = (state == Qt.Checked)
        self._update_preview()
    
    def _on_template_changed(self, index: int):
        """模板改变"""
        if index == 1:  # 科研论文
            self._apply_publication_template()
        elif index == 2:  # 演示文稿
            self._apply_presentation_template()
        elif index == 3:  # 彩色对比
            self._apply_colorful_template()
        else:  # 默认
            self._apply_default_template()
        
        self._update_all_controls()
        self._update_preview()
    
    def _apply_default_template(self):
        """应用默认模板"""
        self.style = PlotStyle()
    
    def _apply_publication_template(self):
        """应用科研论文模板"""
        self.style.line_color = QColor(0, 0, 0)  # 黑色
        self.style.line_width = 2
        self.style.line_style = 'solid'
        self.style.symbol = 'o'
        self.style.symbol_size = 6
        self.style.symbol_color = QColor(0, 0, 0)
        self.style.show_grid = True
        self.style.label_font_size = 14
    
    def _apply_presentation_template(self):
        """应用演示文稿模板"""
        self.style.line_color = QColor(0, 102, 204)  # 深蓝色
        self.style.line_width = 3
        self.style.line_style = 'solid'
        self.style.symbol = 's'
        self.style.symbol_size = 10
        self.style.symbol_color = QColor(0, 102, 204)
        self.style.show_grid = True
        self.style.label_font_size = 16
    
    def _apply_colorful_template(self):
        """应用彩色对比模板"""
        self.style.line_color = QColor(255, 0, 0)  # 红色
        self.style.line_width = 2
        self.style.line_style = 'solid'
        self.style.symbol = 'o'
        self.style.symbol_size = 8
        self.style.symbol_color = QColor(255, 0, 0)
        self.style.show_grid = True
        self.style.label_font_size = 12
    
    def _update_all_controls(self):
        """更新所有控件的值"""
        # 线条
        self._update_color_button(self.line_color_btn, self.style.line_color)
        self.line_color_label.setText(self.style.line_color.name())
        self.line_width_slider.setValue(self.style.line_width)
        self.line_width_label.setText(f"{self.style.line_width} px")
        style_map = {'solid': 0, 'dash': 1, 'dot': 2, 'dashdot': 3}
        self.line_style_combo.setCurrentIndex(style_map.get(self.style.line_style, 0))
        
        # 标记
        symbol_map = {'o': 0, 's': 1, 't': 2, 'd': 3, '+': 4, 'x': 5, 'star': 6}
        self.symbol_combo.setCurrentIndex(symbol_map.get(self.style.symbol, 0))
        self.symbol_size_slider.setValue(self.style.symbol_size)
        self.symbol_size_label.setText(f"{self.style.symbol_size} px")
        self._update_color_button(self.symbol_color_btn, self.style.symbol_color)
        self.symbol_color_label.setText(self.style.symbol_color.name())
        
        # 坐标轴
        self.xlabel_edit.setText(self.style.xlabel)
        self.ylabel_edit.setText(self.style.ylabel)
        self.font_size_slider.setValue(self.style.label_font_size)
        self.font_size_label.setText(f"{self.style.label_font_size} pt")
        self.grid_check.setChecked(self.style.show_grid)
        self.legend_check.setChecked(self.style.show_legend)
    
    def _update_preview(self):
        """更新预览图表"""
        self.preview_plot.clear()
        
        # 设置背景
        self.preview_plot.setBackground('w')
        
        # 设置标签
        self.preview_plot.setLabel('left', self.style.ylabel, **{'font-size': f'{self.style.label_font_size}pt'})
        self.preview_plot.setLabel('bottom', self.style.xlabel, **{'font-size': f'{self.style.label_font_size}pt'})
        
        # 设置网格
        self.preview_plot.showGrid(x=self.style.show_grid, y=self.style.show_grid, alpha=self.style.grid_alpha)
        
        # 线条样式
        pen_styles = {
            'solid': Qt.SolidLine,
            'dash': Qt.DashLine,
            'dot': Qt.DotLine,
            'dashdot': Qt.DashDotLine
        }
        
        pen = pg.mkPen(
            color=(self.style.line_color.red(), self.style.line_color.green(), self.style.line_color.blue()),
            width=self.style.line_width,
            style=pen_styles.get(self.style.line_style, Qt.SolidLine)
        )
        
        # 绘制曲线
        self.preview_plot.plot(
            self.preview_x,
            self.preview_y,
            pen=pen,
            symbol=self.style.symbol,
            symbolSize=self.style.symbol_size,
            symbolBrush=(self.style.symbol_color.red(), self.style.symbol_color.green(), self.style.symbol_color.blue()),
            symbolPen=(self.style.symbol_edge_color.red(), self.style.symbol_edge_color.green(), self.style.symbol_edge_color.blue()),
            name="示例曲线" if self.style.show_legend else None
        )
        
        # 添加图例
        if self.style.show_legend:
            self.preview_plot.addLegend()
    
    def _on_apply(self):
        """应用样式"""
        self.style_applied.emit(self.style.to_dict())
        self.accept()
    
    def _on_reset(self):
        """重置样式"""
        self.style = PlotStyle()
        self.template_combo.setCurrentIndex(0)
        self._update_all_controls()
        self._update_preview()
    
    def get_style(self) -> Dict[str, Any]:
        """获取当前样式"""
        return self.style.to_dict()

