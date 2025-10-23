# -*- coding: utf-8 -*-
"""
SPR传感器数据分析系统 - 完整功能版入口

使用方法：
    python app_full.py
"""
import sys
from pathlib import Path

# 添加src目录到路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication
from src.views import MainWindowFull
from src.controllers import MainControllerFull
import config


def main():
    """应用程序入口 - 完整功能版"""
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName(config.WINDOW_TITLE)
    
    # 设置应用程序图标
    import os
    from PySide6.QtGui import QIcon
    icon_path = os.path.join(os.path.dirname(__file__), 'app_icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # ⭐ 重置JobManager,清除旧任务和回调
    from src.utils.job_manager import JobManager
    JobManager.reset_instance()
    
    # 设置应用样式（可选）
    app.setStyle('Fusion')
    
    # 创建View
    main_window = MainWindowFull()
    
    # 创建Controller（自动连接View和Model）
    controller = MainControllerFull(main_window)
    
    # 显示窗口（默认全屏）
    try:
        main_window.showMaximized()
    except Exception:
        main_window.show()
    
    # 运行事件循环
    exit_code = app.exec()
    
    print("应用程序已退出")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

