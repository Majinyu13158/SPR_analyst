# -*- coding: utf-8 -*-
"""
应用程序配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
TEST_DATA_DIR = BASE_DIR / "tests" / "test_data"

# 日志配置
LOG_DIR = BASE_DIR / "logs"
LOG_LEVEL = "INFO"

# UI配置
WINDOW_TITLE = "SPR Sensor Analyst"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# 绘图样式  
PLOT_STYLE = "default"  # matplotlib样式

# 文件类型过滤器
FILE_FILTERS = "JSON Files (*.json);;Excel Files (*.xlsx);;All Files (*)"

# XlementFitting配置
XLEMENT_FITTING_PATH = BASE_DIR / "XlementFitting"

