#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

log_path = 'fit_trace.log'
if os.path.exists(log_path):
    os.remove(log_path)
    print(f"已删除 {log_path}")

with open(log_path, 'w', encoding='utf-8') as f:
    f.write("")
print(f"已创建空白 {log_path}，请重新运行程序")

