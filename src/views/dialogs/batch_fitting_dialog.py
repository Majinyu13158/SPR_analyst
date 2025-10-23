# -*- coding: utf-8 -*-
"""
批量拟合对话框

功能：
- 显示待拟合数据列表（可勾选）
- 统一或分别设置拟合方法
- 多线程并行拟合
- 实时进度显示
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QComboBox, QProgressBar, QTextEdit, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont


class BatchFittingDialog(QDialog):
    """批量拟合对话框"""
    
    # 信号：开始批量拟合 (data_ids, method, num_threads)
    start_fitting = Signal(list, str, int)
    
    def __init__(self, data_list, available_methods, parent=None):
        """
        初始化对话框
        
        参数:
            data_list: [(data_id, data_name, point_count, is_fittable, reason)]
            available_methods: ["LocalBivariate", "BalanceFitting", ...]
            parent: 父窗口
        """
        super().__init__(parent)
        self.data_list = data_list
        self.available_methods = available_methods
        self.selected_data_ids = []
        
        self._setup_ui()
        self._populate_data_list()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"批量拟合 ({len(self.data_list)}个数据)")
        self.resize(600, 550)
        
        layout = QVBoxLayout(self)
        
        # 数据选择组
        data_group = QGroupBox("待拟合数据")
        data_layout = QVBoxLayout(data_group)
        
        # 提示
        hint_label = QLabel(f"💡 共{len(self.data_list)}个数据，请勾选要拟合的数据：")
        data_layout.addWidget(hint_label)
        
        # 数据列表
        self.data_list_widget = QListWidget()
        self.data_list_widget.setSelectionMode(QListWidget.NoSelection)  # 使用复选框，不需要选择
        data_layout.addWidget(self.data_list_widget)
        
        # 批量操作按钮
        button_row = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._select_all)
        self.deselect_all_btn = QPushButton("全不选")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        self.invert_btn = QPushButton("反选")
        self.invert_btn.clicked.connect(self._invert_selection)
        button_row.addWidget(self.select_all_btn)
        button_row.addWidget(self.deselect_all_btn)
        button_row.addWidget(self.invert_btn)
        button_row.addStretch()
        data_layout.addLayout(button_row)
        
        layout.addWidget(data_group)
        
        # 拟合设置组
        fitting_group = QGroupBox("拟合设置")
        fitting_layout = QVBoxLayout(fitting_group)
        
        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("拟合方法:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(self.available_methods)
        method_row.addWidget(self.method_combo)
        method_row.addStretch()
        fitting_layout.addLayout(method_row)
        
        layout.addWidget(fitting_group)
        
        # 并行设置组
        parallel_group = QGroupBox("性能设置")
        parallel_layout = QVBoxLayout(parallel_group)
        
        self.enable_parallel_check = QCheckBox("启用多线程加速")
        self.enable_parallel_check.setChecked(True)
        self.enable_parallel_check.toggled.connect(self._on_parallel_toggled)
        parallel_layout.addWidget(self.enable_parallel_check)
        
        thread_row = QHBoxLayout()
        thread_row.addWidget(QLabel("  线程数:"))
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 16)
        self.thread_spin.setValue(4)
        self.thread_spin.setSuffix(" 个")
        thread_row.addWidget(self.thread_spin)
        
        import os
        cpu_count = os.cpu_count() or 4
        thread_hint = QLabel(f"(推荐: {cpu_count}核)")
        thread_hint.setStyleSheet("color: gray;")
        thread_row.addWidget(thread_hint)
        thread_row.addStretch()
        parallel_layout.addLayout(thread_row)
        
        layout.addWidget(parallel_group)
        
        # 进度显示组
        progress_group = QGroupBox("进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("等待开始...")
        progress_layout.addWidget(self.status_label)
        
        # 日志文本框（可选，用于显示详细信息）
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        self.log_text.setFont(QFont("Consolas", 9))
        progress_layout.addWidget(self.log_text)
        
        layout.addWidget(progress_group)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.start_btn = QPushButton("开始拟合")
        self.start_btn.setDefault(True)
        self.start_btn.clicked.connect(self._on_start)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _populate_data_list(self):
        """填充数据列表"""
        for data_id, data_name, point_count, is_fittable, reason in self.data_list:
            item = QListWidgetItem()
            
            # 创建复选框项
            if is_fittable:
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)  # 默认选中
                text = f"{data_name} ({point_count}点)"
            else:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # 禁用
                item.setCheckState(Qt.Unchecked)
                text = f"{data_name} - {reason}"
            
            item.setText(text)
            item.setData(Qt.UserRole, data_id)  # 存储data_id
            
            self.data_list_widget.addItem(item)
    
    def _select_all(self):
        """全选"""
        for i in range(self.data_list_widget.count()):
            item = self.data_list_widget.item(i)
            if item.flags() & Qt.ItemIsEnabled:
                item.setCheckState(Qt.Checked)
    
    def _deselect_all(self):
        """全不选"""
        for i in range(self.data_list_widget.count()):
            item = self.data_list_widget.item(i)
            if item.flags() & Qt.ItemIsEnabled:
                item.setCheckState(Qt.Unchecked)
    
    def _invert_selection(self):
        """反选"""
        for i in range(self.data_list_widget.count()):
            item = self.data_list_widget.item(i)
            if item.flags() & Qt.ItemIsEnabled:
                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
    
    def _on_parallel_toggled(self, enabled):
        """多线程开关切换"""
        self.thread_spin.setEnabled(enabled)
    
    def _on_start(self):
        """开始拟合"""
        # 获取选中的数据ID
        selected_ids = []
        for i in range(self.data_list_widget.count()):
            item = self.data_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                data_id = item.data(Qt.UserRole)
                selected_ids.append(data_id)
        
        if not selected_ids:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "未选择数据", "请至少选择一个数据进行拟合")
            return
        
        # 获取拟合方法和线程数
        method = self.method_combo.currentText()
        num_threads = self.thread_spin.value() if self.enable_parallel_check.isChecked() else 1
        
        # 禁用开始按钮，防止重复点击
        self.start_btn.setEnabled(False)
        self.select_all_btn.setEnabled(False)
        self.deselect_all_btn.setEnabled(False)
        self.invert_btn.setEnabled(False)
        
        # 发射信号
        self.selected_data_ids = selected_ids
        self.start_fitting.emit(selected_ids, method, num_threads)
    
    @Slot(int, int, str)
    def update_progress(self, completed, total, current_name=""):
        """
        更新进度
        
        参数:
            completed: 已完成数量
            total: 总数量
            current_name: 当前正在拟合的数据名称
        """
        progress = int(completed / total * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        
        if current_name:
            self.status_label.setText(f"进度: {completed}/{total} - 正在拟合 \"{current_name}\"...")
        else:
            self.status_label.setText(f"进度: {completed}/{total} ({progress}%)")
    
    @Slot(str)
    def append_log(self, message: str):
        """追加日志"""
        self.log_text.append(message)
    
    @Slot(int, int)
    def on_fitting_complete(self, success_count, total_count):
        """
        拟合完成
        
        参数:
            success_count: 成功数量
            total_count: 总数量
        """
        self.progress_bar.setValue(100)
        self.status_label.setText(f"✅ 完成！成功: {success_count}/{total_count}")
        self.start_btn.setEnabled(True)
        self.start_btn.setText("关闭")
        self.start_btn.clicked.disconnect()
        self.start_btn.clicked.connect(self.accept)
        self.cancel_btn.setEnabled(False)

