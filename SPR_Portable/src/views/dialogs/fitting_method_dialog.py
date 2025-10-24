# -*- coding: utf-8 -*-
"""
拟合方法选择对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QSplitter, QWidget,
    QGroupBox, QFormLayout, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from typing import Optional, Dict, Any


class FittingMethodDialog(QDialog):
    """
    拟合方法选择对话框
    
    信号：
        method_selected: (method: str, parameters: dict) 方法被选中
    """
    
    method_selected = Signal(str, dict)
    
    def __init__(self, parent=None, data_manager=None, preselect_data_id=None):
        super().__init__(parent)
        
        self.selected_method: Optional[str] = None
        self.parameters: Dict[str, Any] = {}
        
        # 拟合方法定义
        self.fitting_methods = {
            'LocalBivariate': {
                'name': '局部双变量拟合',
                'description': """
**局部双变量拟合 (Local Bivariate)**

适用于SPR传感器的实时动态分析，通过局部曲线拟合计算结合和解离速率常数。

**特点**：
- 高精度局部拟合
- 适合复杂相互作用
- 可分析多步反应

**参数**：
- 迭代次数：优化算法的迭代次数
- 收敛阈值：拟合收敛的判断标准
                """,
                'parameters': {
                    'max_iter': ('迭代次数', 1000, int, (100, 10000)),
                    'tolerance': ('收敛阈值', 1e-6, float, (1e-10, 1e-3))
                }
            },
            'GlobalBivariate': {
                'name': '全局双变量拟合',
                'description': """
**全局双变量拟合 (Global Bivariate)**

对整个数据集进行全局优化，适用于寻找全局最优解。

**特点**：
- 全局优化算法
- 避免局部最优
- 计算时间较长

**参数**：
- 种群大小：遗传算法的种群规模
- 代数：遗传算法的演化代数
                """,
                'parameters': {
                    'population_size': ('种群大小', 50, int, (10, 200)),
                    'generations': ('代数', 100, int, (10, 500))
                }
            },
            'PartialBivariate': {
                'name': '部分双变量拟合',
                'description': """
**部分双变量拟合 (Partial Bivariate)**

只拟合数据的部分区域，适用于特定阶段的分析。

**特点**：
- 灵活选择拟合区域
- 计算速度快
- 适合初步分析

**参数**：
- 起始点：拟合区域的起始索引
- 结束点：拟合区域的结束索引
                """,
                'parameters': {
                    'start_point': ('起始点', 0, int, (0, 10000)),
                    'end_point': ('结束点', -1, int, (-1, 10000))
                }
            },
            'SingleCycle': {
                'name': '单循环拟合',
                'description': """
**单循环拟合 (Single Cycle)**

针对单次注射-解离循环进行拟合分析。

**特点**：
- 快速分析
- 简化参数
- 适合质量控制

**参数**：
- 基线校正：是否进行基线校正
                """,
                'parameters': {
                    'baseline_correction': ('基线校正', True, bool, None)
                }
            },
            'BalanceFitting': {
                'name': '平衡拟合',
                'description': """
**平衡拟合 (Balance Fitting)**

分析平衡状态下的结合数据，计算平衡解离常数。

**特点**：
- 适用于平衡态分析
- 简单快速
- 提供平衡常数

**参数**：
- 平滑窗口：数据平滑的窗口大小
                """,
                'parameters': {
                    'smooth_window': ('平滑窗口', 5, int, (1, 50))
                }
            }
        }
        
        self.data_manager = data_manager
        self.preselect_data_id = preselect_data_id
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("选择拟合方法")
        self.resize(900, 650)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("🔬 选择拟合方法")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        layout.addWidget(title)
        
        # 分割器（左：方法列表，右：方法说明+参数）
        splitter = QSplitter(Qt.Horizontal)
        
        # ========== 左侧：方法列表 ==========
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("可用方法：")
        list_label.setStyleSheet("font-weight: bold;")
        list_layout.addWidget(list_label)
        
        self.method_list = QListWidget()
        for method_id, method_info in self.fitting_methods.items():
            item = QListWidgetItem(method_info['name'])
            item.setData(Qt.UserRole, method_id)
            self.method_list.addItem(item)
        
        self.method_list.currentItemChanged.connect(self._on_method_changed)
        list_layout.addWidget(self.method_list)
        
        splitter.addWidget(list_widget)
        
        # ========== 右侧：说明+参数 ==========
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 方法说明
        desc_label = QLabel("方法说明：")
        desc_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(desc_label)
        
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(300)
        self.description_text.setStyleSheet("""
            QTextEdit {
                font-size: 11pt;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(self.description_text)
        
        # 参数配置
        param_label = QLabel("参数配置：")
        param_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        right_layout.addWidget(param_label)
        
        self.param_group = QGroupBox()
        self.param_layout = QFormLayout(self.param_group)
        right_layout.addWidget(self.param_group)
        
        right_layout.addStretch()
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 600])
        layout.addWidget(splitter)
        
        # ========== 数据源选择（多选） ==========
        source_group = QGroupBox("数据源选择（可多选，LocalBivariate将合并所选数据列）")
        source_layout = QVBoxLayout(source_group)
        self.data_list = QListWidget()
        self.data_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self._populate_data_sources()
        self.data_list.itemChanged.connect(self._on_data_selection_changed)
        source_layout.addWidget(self.data_list)
        layout.addWidget(source_group)

        # ========== 按钮 ==========
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)
        
        self.ok_btn = QPushButton("开始拟合")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setMinimumWidth(120)
        self.ok_btn.setEnabled(False)
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
        # 默认选中第一个方法
        if self.method_list.count() > 0:
            self.method_list.setCurrentRow(0)
        self._update_ok_enabled()

    def _populate_data_sources(self):
        self.data_list.clear()
        self._data_id_list = []
        if self.data_manager is None:
            item = QListWidgetItem("<无可用数据>")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.data_list.addItem(item)
            return
        try:
            for data_id, data in self.data_manager._data_dict.items():
                try:
                    name = getattr(data, 'name', f'Data {data_id}')
                    df = getattr(data, 'dataframe', None)
                    shape_str = f"{df.shape}" if df is not None and hasattr(df, 'shape') else "(empty)"
                    item = QListWidgetItem(f"[{data_id}] {name}  {shape_str}")
                    item.setData(Qt.UserRole, data_id)
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    # 预选中当前数据
                    if self.preselect_data_id is not None and data_id == self.preselect_data_id:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                    self.data_list.addItem(item)
                    self._data_id_list.append(data_id)
                except Exception:
                    continue
        except Exception:
            item = QListWidgetItem("<数据加载失败>")
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.data_list.addItem(item)

    def _on_data_selection_changed(self, item):
        self._update_ok_enabled()

    def _update_ok_enabled(self):
        has_selected = any(self.data_list.item(i).checkState() == Qt.Checked for i in range(self.data_list.count()))
        self.ok_btn.setEnabled(bool(self.selected_method) and has_selected)
    
    def _on_method_changed(self, current, previous):
        """处理方法选择变化"""
        if not current:
            self.ok_btn.setEnabled(False)
            self.description_text.clear()
            self._clear_parameters()
            return
        
        # 获取选中的方法
        method_id = current.data(Qt.UserRole)
        self.selected_method = method_id
        self._update_ok_enabled()
        
        # 显示方法说明
        method_info = self.fitting_methods[method_id]
        self.description_text.setMarkdown(method_info['description'])
        
        # 显示参数配置
        self._setup_parameters(method_id)
    
    def _setup_parameters(self, method_id: str):
        """设置参数输入控件"""
        self._clear_parameters()
        
        method_info = self.fitting_methods[method_id]
        params = method_info.get('parameters', {})
        
        self.param_widgets = {}
        
        for param_key, param_info in params.items():
            param_name, default_value, param_type, param_range = param_info
            
            if param_type == bool:
                # 布尔参数：使用复选框
                checkbox = QCheckBox()
                checkbox.setChecked(default_value)
                self.param_layout.addRow(param_name + ":", checkbox)
                self.param_widgets[param_key] = checkbox
            
            elif param_type == int:
                # 整数参数：使用SpinBox
                spinbox = QSpinBox()
                spinbox.setValue(default_value)
                if param_range:
                    spinbox.setMinimum(param_range[0])
                    spinbox.setMaximum(param_range[1])
                self.param_layout.addRow(param_name + ":", spinbox)
                self.param_widgets[param_key] = spinbox
            
            elif param_type == float:
                # 浮点参数：使用DoubleSpinBox
                doublespinbox = QDoubleSpinBox()
                doublespinbox.setValue(default_value)
                doublespinbox.setDecimals(10)
                if param_range:
                    doublespinbox.setMinimum(param_range[0])
                    doublespinbox.setMaximum(param_range[1])
                self.param_layout.addRow(param_name + ":", doublespinbox)
                self.param_widgets[param_key] = doublespinbox
            
            else:
                # 字符串参数：使用LineEdit
                lineedit = QLineEdit()
                lineedit.setText(str(default_value))
                self.param_layout.addRow(param_name + ":", lineedit)
                self.param_widgets[param_key] = lineedit
    
    def _clear_parameters(self):
        """清空参数控件"""
        # 移除所有控件
        while self.param_layout.count() > 0:
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.param_widgets = {}
    
    def get_selected_method(self) -> Optional[str]:
        """获取选中的方法"""
        return self.selected_method
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数值"""
        params = {}
        for param_key, widget in self.param_widgets.items():
            if isinstance(widget, QCheckBox):
                params[param_key] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                params[param_key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                params[param_key] = widget.value()
            elif isinstance(widget, QLineEdit):
                params[param_key] = widget.text()
        
        return params

    def get_selected_data_ids(self):
        ids = []
        for i in range(self.data_list.count()):
            item = self.data_list.item(i)
            if item.checkState() == Qt.Checked:
                ids.append(item.data(Qt.UserRole))
        return ids


# ========== 便利函数 ==========

def select_fitting_method(parent=None, data_manager=None, preselect_data_id=None) -> tuple[Optional[str], Dict[str, Any], list]:
    """
    显示拟合方法选择对话框（便利函数）
    
    参数:
        parent: 父窗口
    
    返回:
        (method, parameters)，如果取消则返回(None, {})
    """
    dialog = FittingMethodDialog(parent, data_manager=data_manager, preselect_data_id=preselect_data_id)
    if dialog.exec() == QDialog.Accepted:
        return dialog.get_selected_method(), dialog.get_parameters(), dialog.get_selected_data_ids()
    
    return None, {}, []

