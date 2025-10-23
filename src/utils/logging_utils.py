# -*- coding: utf-8 -*-
"""
简单文件追踪日志：用于定位拟合触发来源。
"""
from datetime import datetime
import os
import threading


def append_fit_trace(message: str):
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        tid = threading.get_ident()
        line = f"[{ts}] [tid={tid}] {message}\n"
        path = os.path.join(os.getcwd(), 'fit_trace.log')
        with open(path, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass


