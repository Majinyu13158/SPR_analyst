# -*- coding: utf-8 -*-
"""
数据血缘（Provenance）模块

提供操作记录、血缘追踪和历史管理功能
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import uuid


@dataclass
class OperationLog:
    """单个操作的完整记录"""
    op_id: str                          # 操作唯一ID（UUID）
    op_type: str                        # 操作类型：import, fit, transform, delete, create_figure
    timestamp: str                      # ISO格式时间戳
    
    # 输入输出
    inputs: Dict[str, Any]              # {'data_id': 0, 'method': 'LocalBivariate'}
    outputs: Dict[str, Any]             # {'result_id': 1, 'fitted_data_id': 2, 'figure_id': 3}
    
    # 元数据
    description: str                    # 人类可读描述："拟合数据#0，使用LocalBivariate"
    user: Optional[str] = None          # 用户标识（可选）
    
    # 状态
    status: str = 'success'             # 'success', 'failed', 'reverted'
    error: Optional[str] = None         # 错误信息（如果失败）
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OperationLog':
        """从字典创建"""
        return cls(**data)


class ProvenanceManager:
    """管理操作历史和数据血缘"""
    
    def __init__(self):
        self._operations: List[OperationLog] = []
        # key: ('data', 0) -> value: [op_id1, op_id2, ...]  # 影响这个对象的所有操作
        self._object_lineage: Dict[Tuple[str, int], List[str]] = {}
    
    def record_operation(self, op_log: OperationLog):
        """
        记录一个操作
        
        Args:
            op_log: 操作日志
        """
        self._operations.append(op_log)
        self._update_lineage(op_log)
    
    def _update_lineage(self, op_log: OperationLog):
        """更新对象血缘关系"""
        # 记录输入对象的血缘
        for key, value in op_log.inputs.items():
            if key.endswith('_id') and isinstance(value, int):
                obj_type = key.replace('_id', '')
                self._add_to_lineage(obj_type, value, op_log.op_id)
            elif key.endswith('_ids') and isinstance(value, list):
                obj_type = key.replace('_ids', '').rstrip('s')  # data_ids -> data
                for obj_id in value:
                    if isinstance(obj_id, int):
                        self._add_to_lineage(obj_type, obj_id, op_log.op_id)
        
        # 记录输出对象的血缘
        for key, value in op_log.outputs.items():
            if key.endswith('_id') and isinstance(value, int):
                obj_type = key.replace('_id', '')
                self._add_to_lineage(obj_type, value, op_log.op_id)
            elif key.endswith('_ids') and isinstance(value, list):
                obj_type = key.replace('_ids', '').rstrip('s')
                for obj_id in value:
                    if isinstance(obj_id, int):
                        self._add_to_lineage(obj_type, obj_id, op_log.op_id)
    
    def _add_to_lineage(self, obj_type: str, obj_id: int, op_id: str):
        """添加对象到血缘记录"""
        key = (obj_type, obj_id)
        if key not in self._object_lineage:
            self._object_lineage[key] = []
        if op_id not in self._object_lineage[key]:
            self._object_lineage[key].append(op_id)
    
    def get_lineage(self, obj_type: str, obj_id: int) -> List[OperationLog]:
        """
        获取某个对象的完整血缘
        
        Args:
            obj_type: 对象类型 ('data', 'figure', 'result')
            obj_id: 对象ID
        
        Returns:
            影响该对象的所有操作日志（按时间顺序）
        """
        key = (obj_type, obj_id)
        op_ids = self._object_lineage.get(key, [])
        return [op for op in self._operations if op.op_id in op_ids]
    
    def get_all_operations(self) -> List[OperationLog]:
        """获取所有操作记录"""
        return self._operations.copy()
    
    def get_operation_by_id(self, op_id: str) -> Optional[OperationLog]:
        """根据ID获取操作记录"""
        for op in self._operations:
            if op.op_id == op_id:
                return op
        return None
    
    def mark_reverted(self, op_id: str):
        """标记操作已被撤销"""
        op = self.get_operation_by_id(op_id)
        if op:
            op.status = 'reverted'
    
    def export_lineage(self, obj_type: str, obj_id: int, format: str = 'json') -> str:
        """
        导出血缘图
        
        Args:
            obj_type: 对象类型
            obj_id: 对象ID
            format: 导出格式 ('json', 'text')
        
        Returns:
            格式化的血缘信息
        """
        lineage = self.get_lineage(obj_type, obj_id)
        
        if format == 'json':
            return json.dumps([op.to_dict() for op in lineage], indent=2, ensure_ascii=False)
        
        elif format == 'text':
            lines = [f"血缘追踪: {obj_type}#{obj_id}"]
            lines.append("=" * 60)
            for i, op in enumerate(lineage, 1):
                lines.append(f"\n步骤 {i}: {op.description}")
                lines.append(f"  时间: {op.timestamp}")
                lines.append(f"  操作: {op.op_type}")
                lines.append(f"  状态: {op.status}")
                if op.inputs:
                    lines.append(f"  输入: {op.inputs}")
                if op.outputs:
                    lines.append(f"  输出: {op.outputs}")
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_all(self, format: str = 'json') -> str:
        """
        导出所有操作历史
        
        Args:
            format: 导出格式 ('json', 'text')
        
        Returns:
            格式化的历史信息
        """
        if format == 'json':
            return json.dumps([op.to_dict() for op in self._operations], 
                            indent=2, ensure_ascii=False)
        
        elif format == 'text':
            lines = ["操作历史"]
            lines.append("=" * 60)
            for i, op in enumerate(self._operations, 1):
                lines.append(f"\n{i}. {op.description}")
                lines.append(f"   时间: {op.timestamp}")
                lines.append(f"   操作: {op.op_type}")
                lines.append(f"   状态: {op.status}")
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def clear(self):
        """清空所有记录"""
        self._operations.clear()
        self._object_lineage.clear()
    
    def save_to_file(self, file_path: str):
        """保存到JSON文件"""
        data = {
            'operations': [op.to_dict() for op in self._operations],
            'object_lineage': {
                f"{k[0]}_{k[1]}": v for k, v in self._object_lineage.items()
            }
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, file_path: str):
        """从JSON文件加载"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._operations = [OperationLog.from_dict(op) for op in data['operations']]
        
        self._object_lineage = {}
        for key_str, op_ids in data['object_lineage'].items():
            obj_type, obj_id_str = key_str.rsplit('_', 1)
            obj_id = int(obj_id_str)
            self._object_lineage[(obj_type, obj_id)] = op_ids

