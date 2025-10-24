# -*- coding: utf-8 -*-
"""
数据导出对话框

功能：
- 选择导出格式（Excel/CSV/JSON）
- 选择保存路径
- 导出选项设置
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QRadioButton, QLineEdit, QPushButton, QLabel,
    QCheckBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from pathlib import Path


class ExportDialog(QDialog):
    """数据导出对话框"""
    
    def __init__(self, data_name: str, default_dir: str = None, parent=None):
        """
        初始化对话框
        
        参数:
            data_name: 数据名称
            default_dir: 默认导出目录
            parent: 父窗口
        """
        super().__init__(parent)
        self.data_name = data_name
        self.default_dir = default_dir or str(Path.cwd() / 'exports')
        
        self.selected_format = 'xlsx'  # 默认Excel
        self.selected_path = ''
        self.include_metadata = True
        
        self._setup_ui()
        self._update_default_path()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"导出数据: {self.data_name}")
        self.resize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # 格式选择组
        format_group = QGroupBox("导出格式")
        format_layout = QVBoxLayout(format_group)
        
        self.radio_excel = QRadioButton("Excel (.xlsx) [推荐]")
        self.radio_excel.setChecked(True)
        self.radio_excel.toggled.connect(self._on_format_changed)
        
        self.radio_csv = QRadioButton("CSV (.csv)")
        self.radio_csv.toggled.connect(self._on_format_changed)
        
        self.radio_json = QRadioButton("JSON (.json) [包含完整信息]")
        self.radio_json.toggled.connect(self._on_format_changed)
        
        format_layout.addWidget(self.radio_excel)
        format_layout.addWidget(self.radio_csv)
        format_layout.addWidget(self.radio_json)
        
        layout.addWidget(format_group)
        
        # 保存路径组
        path_group = QGroupBox("保存位置")
        path_layout = QVBoxLayout(path_group)
        
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择保存路径...")
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_path)
        
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_btn)
        
        path_layout.addLayout(path_row)
        
        # 提示信息
        self.path_hint = QLabel(f"💡 默认导出到项目的 exports 文件夹")
        self.path_hint.setStyleSheet("color: gray; font-size: 10pt;")
        path_layout.addWidget(self.path_hint)
        
        layout.addWidget(path_group)
        
        # 选项组
        options_group = QGroupBox("导出选项")
        options_layout = QVBoxLayout(options_group)
        
        self.check_metadata = QCheckBox("包含元数据（Excel: 额外工作表 | JSON: 属性信息）")
        self.check_metadata.setChecked(True)
        self.check_metadata.stateChanged.connect(self._on_metadata_changed)
        
        options_layout.addWidget(self.check_metadata)
        
        layout.addWidget(options_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        export_btn = QPushButton("导出")
        export_btn.setDefault(True)
        export_btn.clicked.connect(self._on_export)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(export_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _on_format_changed(self):
        """格式选择改变"""
        if self.radio_excel.isChecked():
            self.selected_format = 'xlsx'
            self.check_metadata.setEnabled(True)
        elif self.radio_csv.isChecked():
            self.selected_format = 'csv'
            self.check_metadata.setEnabled(False)
            self.check_metadata.setChecked(False)
        elif self.radio_json.isChecked():
            self.selected_format = 'json'
            self.check_metadata.setEnabled(True)
            self.check_metadata.setChecked(True)  # JSON默认包含元数据
        
        self._update_default_path()
    
    def _on_metadata_changed(self):
        """元数据选项改变"""
        self.include_metadata = self.check_metadata.isChecked()
    
    def _update_default_path(self):
        """更新默认路径"""
        from src.utils.data_exporter import DataExporter
        
        # 生成文件名（简化版）
        clean_name = DataExporter.sanitize_filename(self.data_name)
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{clean_name}_{timestamp}.{self.selected_format}"
        
        # 组合完整路径
        full_path = str(Path(self.default_dir) / filename)
        self.path_edit.setText(full_path)
    
    def _browse_path(self):
        """浏览保存路径"""
        # 根据格式选择文件过滤器
        if self.selected_format == 'xlsx':
            filter_str = "Excel文件 (*.xlsx);;所有文件 (*.*)"
            default_ext = ".xlsx"
        elif self.selected_format == 'csv':
            filter_str = "CSV文件 (*.csv);;所有文件 (*.*)"
            default_ext = ".csv"
        else:  # json
            filter_str = "JSON文件 (*.json);;所有文件 (*.*)"
            default_ext = ".json"
        
        # 获取当前路径作为默认
        current_path = self.path_edit.text()
        if not current_path:
            current_path = str(Path(self.default_dir) / f"{self.data_name}{default_ext}")
        
        # 打开文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择保存位置",
            current_path,
            filter_str
        )
        
        if file_path:
            self.path_edit.setText(file_path)
    
    def _on_export(self):
        """确认导出"""
        path = self.path_edit.text().strip()
        
        if not path:
            QMessageBox.warning(self, "路径错误", "请选择保存路径")
            return
        
        # 检查文件是否已存在
        if Path(path).exists():
            reply = QMessageBox.question(
                self,
                "文件已存在",
                f"文件已存在:\n{path}\n\n是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.selected_path = path
        self.accept()
    
    def get_export_settings(self):
        """
        获取导出设置
        
        返回:
            dict: {
                'format': 'xlsx'|'csv'|'json',
                'path': '文件路径',
                'include_metadata': True|False
            }
        """
        return {
            'format': self.selected_format,
            'path': self.selected_path,
            'include_metadata': self.include_metadata
        }

