# -*- coding: utf-8 -*-
"""
可在进程池中调用的纯函数任务（可pickle）。
"""
from typing import Any, Dict


def run_fit_task(method: str, x_data, y_data, dataframe) -> Dict[str, Any]:
    """子进程可执行的拟合任务。
    不接受 GUI/Data 对象，只接受可序列化的数据结构。
    """
    from src.utils.fitting_wrapper import fit_data as _fit
    return _fit(method, x_data, y_data, dataframe=dataframe)


