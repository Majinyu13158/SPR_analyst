# -*- coding: utf-8 -*-
"""
图表导出对话框

功能：
- 选择导出格式（PNG/PDF/SVG/JPG）
- 选择保存路径
- 设置图片分辨率
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QRadioButton, QLineEdit, QPushButton, QLabel,
    QSpinBox, QFileDialog, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from pathlib import Path


class ExportFigureDialog(QDialog):
    """图表导出对话框"""
    
    # 预设分辨率
    RESOLUTION_PRESETS = {
        '标准 (1280×720)': (1280, 720),
        '高清 (1920×1080)': (1920, 1080),
        '2K (2560×1440)': (2560, 1440),
        '4K (3840×2160)': (3840, 2160),
        '论文 (3000×2000)': (3000, 2000),
        '自定义': None
    }
    
    def __init__(self, figure_name: str, default_dir: str = None, parent=None):
        """
        初始化对话框
        
        参数:
            figure_name: 图表名称
            default_dir: 默认导出目录
            parent: 父窗口
        """
        super().__init__(parent)
        self.figure_name = figure_name
        self.default_dir = default_dir or str(Path.cwd() / 'exports')
        
        self.selected_format = 'png'  # 默认PNG
        self.selected_path = ''
        self.width = 1920
        self.height = 1080
        
        self._setup_ui()
        self._update_default_path()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle(f"导出图表: {self.figure_name}")
        self.resize(500, 350)
        
        layout = QVBoxLayout(self)
        
        # 格式选择组
        format_group = QGroupBox("导出格式")
        format_layout = QVBoxLayout(format_group)
        
        self.radio_png = QRadioButton("PNG (.png) [推荐，无损高质量]")
        self.radio_png.setChecked(True)
        self.radio_png.toggled.connect(self._on_format_changed)
        
        self.radio_pdf = QRadioButton("PDF (.pdf) [论文、报告]")
        self.radio_pdf.toggled.connect(self._on_format_changed)
        
        self.radio_svg = QRadioButton("SVG (.svg) [矢量格式，可编辑]")
        self.radio_svg.toggled.connect(self._on_format_changed)
        
        self.radio_jpg = QRadioButton("JPG (.jpg) [文件更小，有损]")
        self.radio_jpg.toggled.connect(self._on_format_changed)
        
        format_layout.addWidget(self.radio_png)
        format_layout.addWidget(self.radio_pdf)
        format_layout.addWidget(self.radio_svg)
        format_layout.addWidget(self.radio_jpg)
        
        layout.addWidget(format_group)
        
        # 分辨率设置组
        resolution_group = QGroupBox("图片分辨率")
        resolution_layout = QVBoxLayout(resolution_group)
        
        # 预设分辨率下拉框
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("预设:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(list(self.RESOLUTION_PRESETS.keys()))
        self.resolution_combo.setCurrentText('高清 (1920×1080)')
        self.resolution_combo.currentTextChanged.connect(self._on_resolution_preset_changed)
        preset_row.addWidget(self.resolution_combo)
        resolution_layout.addLayout(preset_row)
        
        # 自定义分辨率
        custom_row = QHBoxLayout()
        custom_row.addWidget(QLabel("宽度:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 10000)
        self.width_spin.setValue(1920)
        self.width_spin.setSuffix(" px")
        custom_row.addWidget(self.width_spin)
        
        custom_row.addWidget(QLabel("高度:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 10000)
        self.height_spin.setValue(1080)
        self.height_spin.setSuffix(" px")
        custom_row.addWidget(self.height_spin)
        custom_row.addStretch()
        resolution_layout.addLayout(custom_row)
        
        # 提示
        hint_label = QLabel("💡 分辨率越高，图片越清晰，但文件也越大")
        hint_label.setStyleSheet("color: gray; font-size: 10pt;")
        resolution_layout.addWidget(hint_label)
        
        # SVG提示
        self.svg_hint = QLabel("⚠️ SVG为矢量格式，不受分辨率限制")
        self.svg_hint.setStyleSheet("color: orange; font-size: 10pt;")
        self.svg_hint.setVisible(False)
        resolution_layout.addWidget(self.svg_hint)
        
        layout.addWidget(resolution_group)
        
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
        if self.radio_png.isChecked():
            self.selected_format = 'png'
        elif self.radio_pdf.isChecked():
            self.selected_format = 'pdf'
        elif self.radio_svg.isChecked():
            self.selected_format = 'svg'
        elif self.radio_jpg.isChecked():
            self.selected_format = 'jpg'
        
        # SVG格式显示特殊提示
        is_svg = self.selected_format == 'svg'
        self.svg_hint.setVisible(is_svg)
        self.width_spin.setEnabled(not is_svg)
        self.height_spin.setEnabled(not is_svg)
        self.resolution_combo.setEnabled(not is_svg)
        
        self._update_default_path()
    
    def _on_resolution_preset_changed(self, preset_name: str):
        """预设分辨率改变"""
        resolution = self.RESOLUTION_PRESETS.get(preset_name)
        if resolution:
            width, height = resolution
            self.width_spin.setValue(width)
            self.height_spin.setValue(height)
    
    def _update_default_path(self):
        """更新默认路径"""
        from datetime import datetime
        
        # 清理文件名
        clean_name = self.figure_name
        for char in r'/\:*?"<>|':
            clean_name = clean_name.replace(char, '_')
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{clean_name}_{timestamp}.{self.selected_format}"
        
        # 组合完整路径
        full_path = str(Path(self.default_dir) / filename)
        self.path_edit.setText(full_path)
    
    def _browse_path(self):
        """浏览保存路径"""
        # 根据格式选择文件过滤器
        if self.selected_format == 'png':
            filter_str = "PNG图片 (*.png);;所有文件 (*.*)"
            default_ext = ".png"
        elif self.selected_format == 'pdf':
            filter_str = "PDF文档 (*.pdf);;所有文件 (*.*)"
            default_ext = ".pdf"
        elif self.selected_format == 'svg':
            filter_str = "SVG矢量图 (*.svg);;所有文件 (*.*)"
            default_ext = ".svg"
        else:  # jpg
            filter_str = "JPG图片 (*.jpg *.jpeg);;所有文件 (*.*)"
            default_ext = ".jpg"
        
        # 获取当前路径作为默认
        current_path = self.path_edit.text()
        if not current_path:
            current_path = str(Path(self.default_dir) / f"{self.figure_name}{default_ext}")
        
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
        
        # 保存设置
        self.selected_path = path
        self.width = self.width_spin.value()
        self.height = self.height_spin.value()
        
        self.accept()
    
    def get_export_settings(self):
        """
        获取导出设置
        
        返回:
            dict: {
                'format': 'png'|'pdf'|'svg'|'jpg',
                'path': '文件路径',
                'width': 1920,
                'height': 1080
            }
        """
        return {
            'format': self.selected_format,
            'path': self.selected_path,
            'width': self.width,
            'height': self.height
        }

