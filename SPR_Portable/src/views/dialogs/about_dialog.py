# -*- coding: utf-8 -*-
"""
关于对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import config


class AboutDialog(QDialog):
    """
    关于对话框
    
    显示应用程序信息
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(500, 400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 应用名称
        title = QLabel(config.WINDOW_TITLE)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 版本信息
        version = QLabel("Version 2.0 - 重构版")
        version.setStyleSheet("color: #666; font-size: 14px;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        # 描述
        description = QTextBrowser()
        description.setHtml("""
        <div style='text-align: center;'>
        <h3>SPR传感器数据分析系统</h3>
        <p><b>功能特性:</b></p>
        <ul style='text-align: left; margin-left: 100px;'>
            <li>支持多种数据格式（JSON, Excel）</li>
            <li>强大的数据可视化</li>
            <li>多种拟合算法（LocalBivariate, GlobalBivariate等）</li>
            <li>项目管理功能</li>
            <li>结果导出</li>
        </ul>
        <p><b>技术栈:</b></p>
        <ul style='text-align: left; margin-left: 100px;'>
            <li>PySide6 - GUI框架</li>
            <li>qfluentwidgets - 现代UI组件</li>
            <li>Matplotlib - 数据可视化</li>
            <li>NumPy & Pandas - 科学计算</li>
            <li>SciPy - 拟合算法</li>
        </ul>
        <p><b>架构:</b> MVC (Model-View-Controller)</p>
        <hr>
        <p style='color: #666; font-size: 12px;'>
        © 2025 SPR Project Team<br>
        All Rights Reserved
        </p>
        </div>
        """)
        description.setOpenExternalLinks(True)
        layout.addWidget(description)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        close_button.setFixedWidth(100)
        button_layout = QVBoxLayout()
        button_layout.addWidget(close_button, alignment=Qt.AlignCenter)
        layout.addLayout(button_layout)

