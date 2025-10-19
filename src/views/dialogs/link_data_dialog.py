# -*- coding: utf-8 -*-
"""
数据关联对话框 - 用于选择要关联的数据对象
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QSplitter, QWidget
)
from PySide6.QtCore import Qt, Signal
from typing import Optional, Dict, Any
import pandas as pd


class LinkDataDialog(QDialog):
    """
    数据关联对话框
    
    信号：
        data_selected: (data_id: int) 数据被选中
    """
    
    data_selected = Signal(int)
    
    def __init__(self, data_list: Dict[int, Dict[str, Any]], parent=None):
        """
        初始化对话框
        
        参数:
            data_list: {data_id: {'name': str, 'dataframe': pd.DataFrame, ...}}
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.data_list = data_list
        self.selected_data_id: Optional[int] = None
        
        self._setup_ui()
        self._load_data_list()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("选择数据源")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("📊 选择要关联的数据")
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
        
        # 分割器（上：数据列表，下：数据预览）
        splitter = QSplitter(Qt.Vertical)
        
        # ========== 数据列表 ==========
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("可用数据：")
        list_label.setStyleSheet("font-weight: bold;")
        list_layout.addWidget(list_label)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["ID", "名称", "行数", "列数"])
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setSelectionMode(QTableWidget.SingleSelection)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.data_table.currentItemChanged.connect(self._on_selection_changed)
        list_layout.addWidget(self.data_table)
        
        splitter.addWidget(list_widget)
        
        # ========== 数据预览 ==========
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("数据预览：")
        preview_label.setStyleSheet("font-weight: bold;")
        preview_layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                background-color: #f5f5f5;
            }
        """)
        preview_layout.addWidget(self.preview_text)
        
        splitter.addWidget(preview_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 300])
        layout.addWidget(splitter)
        
        # ========== 按钮 ==========
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setMinimumWidth(100)
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
    
    def _load_data_list(self):
        """加载数据列表"""
        self.data_table.setRowCount(len(self.data_list))
        
        for row, (data_id, data_info) in enumerate(self.data_list.items()):
            # ID
            id_item = QTableWidgetItem(str(data_id))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.data_table.setItem(row, 0, id_item)
            
            # 名称
            name_item = QTableWidgetItem(data_info.get('name', f"Data {data_id}"))
            self.data_table.setItem(row, 1, name_item)
            
            # 行数和列数
            df = data_info.get('dataframe')
            if df is not None and isinstance(df, pd.DataFrame):
                rows_item = QTableWidgetItem(str(len(df)))
                rows_item.setTextAlignment(Qt.AlignCenter)
                self.data_table.setItem(row, 2, rows_item)
                
                cols_item = QTableWidgetItem(str(len(df.columns)))
                cols_item.setTextAlignment(Qt.AlignCenter)
                self.data_table.setItem(row, 3, cols_item)
            else:
                self.data_table.setItem(row, 2, QTableWidgetItem("N/A"))
                self.data_table.setItem(row, 3, QTableWidgetItem("N/A"))
        
        # 调整列宽
        self.data_table.resizeColumnsToContents()
        self.data_table.setColumnWidth(1, 250)  # 名称列宽一些
    
    def _on_selection_changed(self, current, previous):
        """处理选择变化"""
        if not current:
            self.ok_btn.setEnabled(False)
            self.preview_text.clear()
            return
        
        # 获取选中的数据ID
        row = current.row()
        data_id_item = self.data_table.item(row, 0)
        if data_id_item:
            self.selected_data_id = int(data_id_item.text())
            self.ok_btn.setEnabled(True)
            
            # 显示预览
            self._show_preview(self.selected_data_id)
    
    def _show_preview(self, data_id: int):
        """显示数据预览"""
        data_info = self.data_list.get(data_id)
        if not data_info:
            self.preview_text.setText("无法获取数据信息")
            return
        
        df = data_info.get('dataframe')
        if df is None or not isinstance(df, pd.DataFrame):
            self.preview_text.setText("数据不可用")
            return
        
        # 构建预览文本
        preview_lines = []
        preview_lines.append(f"数据名称: {data_info.get('name', 'Unknown')}")
        preview_lines.append(f"数据ID: {data_id}")
        preview_lines.append(f"形状: {df.shape[0]} 行 × {df.shape[1]} 列")
        preview_lines.append(f"列名: {', '.join(df.columns.tolist())}")
        preview_lines.append("")
        preview_lines.append("前5行数据：")
        preview_lines.append("-" * 60)
        preview_lines.append(df.head().to_string())
        
        # 如果有attrs（元数据）
        if hasattr(df, 'attrs') and df.attrs:
            preview_lines.append("")
            preview_lines.append("元数据：")
            preview_lines.append("-" * 60)
            for key, value in df.attrs.items():
                preview_lines.append(f"  {key}: {value}")
        
        self.preview_text.setText("\n".join(preview_lines))
    
    def get_selected_data_id(self) -> Optional[int]:
        """获取选中的数据ID"""
        return self.selected_data_id


# ========== 便利函数 ==========

def select_data(data_manager, parent=None) -> Optional[int]:
    """
    显示数据选择对话框（便利函数）
    
    参数:
        data_manager: DataManager实例
        parent: 父窗口
    
    返回:
        选中的data_id，如果取消则返回None
    """
    # 构建数据列表
    data_list = {}
    for data_id, data_obj in data_manager._data_dict.items():
        data_list[data_id] = {
            'name': data_obj.get_name(),
            'dataframe': data_obj.get_processed_data()
        }
    
    # 如果没有数据
    if not data_list:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(parent, "没有可用数据", "请先导入或创建数据")
        return None
    
    # 显示对话框
    dialog = LinkDataDialog(data_list, parent)
    if dialog.exec() == QDialog.Accepted:
        return dialog.get_selected_data_id()
    
    return None

