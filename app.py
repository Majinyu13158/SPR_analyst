# -*- coding: utf-8 -*-
"""
SPR传感器数据分析系统 - MVP版本入口

这是重构后的新版本入口文件，采用标准MVC架构
"""
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication
from src.views import MainWindow
from src.controllers import MainController
import config


def main():
    """应用程序主入口"""
    print("=" * 60)
    print("🚀 SPR Sensor Analyst - MVP版本")
    print("=" * 60)
    print(f"📦 版本: 2.0.0-MVP")
    print(f"🏗️  架构: MVC (Model-View-Controller)")
    print(f"📂 项目目录: {config.BASE_DIR}")
    print("=" * 60)
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName(config.WINDOW_TITLE)
    app.setStyle('Fusion')  # 使用Fusion样式
    
    print("\n🔧 正在初始化...")
    
    # 创建View
    print("  ├─ 创建View...")
    main_window = MainWindow()
    
    # 创建Controller（自动连接View和Model）
    print("  ├─ 创建Controller...")
    controller = MainController(main_window)
    
    print("  └─ 初始化完成！\n")
    
    # 显示窗口
    print("🖥️  显示主窗口...")
    main_window.show()
    
    print("\n✨ 应用程序启动成功！")
    print("=" * 60)
    print("\n💡 使用提示:")
    print("  • 在右侧区域拖拽或点击选择JSON文件")
    print("  • 数据将显示在左侧列表中")
    print("  • 点击'数据详情'标签查看详细信息\n")
    
    # 运行事件循环
    exit_code = app.exec()
    
    print("\n👋 应用程序已退出")
    print("=" * 60)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

