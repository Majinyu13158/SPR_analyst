# -*- coding: utf-8 -*-
"""
JSON读取工具 - 从旧版本移植
"""
import json
from typing import Dict, Any


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """展平嵌套字典"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def read_and_parse_json(file_path: str) -> Dict[str, Any]:
    """读取并解析JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return flatten_dict(data)


def json_reader(file_path: str) -> Dict[str, Any]:
    """
    JSON读取器主函数
    
    参数:
        file_path: JSON文件路径
    
    返回:
        Dict: 解析后的数据
    """
    data = read_and_parse_json(file_path)
    return data


# 为兼容性添加别名
def read_json(file_path: str) -> Dict[str, Any]:
    """
    读取JSON文件（返回原始未展平的JSON数据）
    
    参数:
        file_path: JSON文件路径
    
    返回:
        Dict: 原始JSON数据（未展平）
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

