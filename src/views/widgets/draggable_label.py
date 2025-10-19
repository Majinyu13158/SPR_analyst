# -*- coding: utf-8 -*-
"""
可拖拽标签组件 - MVP简化版
"""
from PySide6.QtWidgets import QLabel, QFileDialog
from PySide6.QtCore import Qt, Signal


class DraggableLabel(QLabel):
    """
    可拖拽文件的标签组件
    
    信号:
        file_selected: 文件被选择，参数(文件路径)
    """
    file_selected = Signal(str)
    
    def __init__(self, text: str = "拖拽文件到这里或点击选择", parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(300, 200)
        self._apply_style()
    
    def _apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px dashed #cccccc;
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
                color: #666666;
            }
            QLabel:hover {
                background-color: #e8e8e8;
                border-color: #999999;
            }
        """)
    
    def mousePressEvent(self, event):
        """鼠标点击 - 打开文件对话框"""
        if event.button() == Qt.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择文件", 
                "",
                "JSON Files (*.json);;Excel Files (*.xlsx);;All Files (*)"
            )
            if file_path:
                self.setText(f"已选择:\n{file_path}")
                self.file_selected.emit(file_path)
    
    def dragEnterEvent(self, event):
        """拖拽进入"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """拖拽放下"""
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.setText(f"已选择:\n{file_path}")
            self.file_selected.emit(file_path)
            event.accept()

