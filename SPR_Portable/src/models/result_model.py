# -*- coding: utf-8 -*-
"""
结果模型 - 从旧版本迁移

原始文件: spr_app_model_main.py - Result类
"""
from PySide6.QtCore import QObject, Signal
from typing import Optional, Dict, Any
from datetime import datetime


class FittingResult(QObject):
    """
    拟合结果类
    
    存储拟合参数和统计信息
    
    信号：
        result_updated: 结果更新
        data_source_changed: 数据源改变 (data_id)
    """
    
    result_updated = Signal()
    data_source_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 基本信息
        self.id: int = 0
        self.name: str = ""
        self.method: str = ""  # LocalBivariate, GlobalBivariate等
        self.created_time: datetime = datetime.now()
        
        # 拟合参数
        self.parameters: Dict[str, Any] = {}
        # 例如：
        # {
        #     'Ka': (1.5e5, 1.2e4, 'M-1s-1'),  # (value, error, unit)
        #     'Kd': (2.3e-3, 1.1e-4, 's-1'),
        #     'KD': (15.3, 0.8, 'nM'),
        #     'Rmax': (100.5, 2.3, 'RU'),
        #     'Chi2': (0.85, None, None)
        # }
        
        # 统计信息
        self.chi_squared: Optional[float] = None
        self.r_squared: Optional[float] = None
        self.rmse: Optional[float] = None
        
        # 关联信息
        self.data_id: Optional[int] = None
        self.figure_id: Optional[int] = None
        
        # 备注
        self.notes: str = ""
    
    def set_parameters(self, params: Dict[str, Any]):
        """设置拟合参数"""
        self.parameters = params
        self.result_updated.emit()
    
    def set_statistics(self, chi2=None, r2=None, rmse=None):
        """设置统计信息"""
        if chi2 is not None:
            self.chi_squared = chi2
        if r2 is not None:
            self.r_squared = r2
        if rmse is not None:
            self.rmse = rmse
        self.result_updated.emit()
    
    def get_parameter_value(self, param_name: str) -> Optional[float]:
        """获取参数值"""
        if param_name in self.parameters:
            value = self.parameters[param_name]
            if isinstance(value, (tuple, list)):
                return value[0]
            return value
        return None
    
    def set_data_source(self, data_id: int):
        """
        设置数据源并发射信号
        
        参数：
            data_id: 关联的数据ID
        """
        old_data_id = self.data_id
        self.data_id = data_id
        
        if old_data_id != data_id:
            self.data_source_changed.emit(data_id)
            self.result_updated.emit()
            print(f"[FittingResult] {self.name} 数据源更改: {old_data_id} → {data_id}")
    
    def get_data_source(self) -> Optional[int]:
        """
        获取关联的数据ID
        
        返回：
            Optional[int]: 数据ID，如果未关联则返回None
        """
        return self.data_id
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'method': self.method,
            'created_time': self.created_time.isoformat(),
            'parameters': self.parameters,
            'chi_squared': self.chi_squared,
            'r_squared': self.r_squared,
            'rmse': self.rmse,
            'data_id': self.data_id,
            'figure_id': self.figure_id,
            'notes': self.notes
        }


class ResultManager(QObject):
    """
    结果管理器
    
    管理所有拟合结果
    
    信号：
        result_added: 结果添加 (result_id)
        result_removed: 结果删除 (result_id)
        result_updated: 结果更新 (result_id)
    """
    
    result_added = Signal(int)
    result_removed = Signal(int)
    result_updated = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = {}  # {id: FittingResult}
        self._next_id = 1
    
    def add_result(self, name: str, method: str) -> int:
        """
        添加结果
        
        返回:
            result_id
        """
        result = FittingResult(self)
        result.id = self._next_id
        result.name = name
        result.method = method
        result.created_time = datetime.now()
        
        self._results[self._next_id] = result
        
        # 连接信号
        result.result_updated.connect(
            lambda: self.result_updated.emit(result.id)
        )
        
        self.result_added.emit(self._next_id)
        
        self._next_id += 1
        return result.id
    
    def get_result(self, result_id: int) -> Optional[FittingResult]:
        """获取结果"""
        return self._results.get(result_id)
    
    def remove_result(self, result_id: int):
        """删除结果"""
        if result_id in self._results:
            del self._results[result_id]
            self.result_removed.emit(result_id)
    
    def get_all_results(self) -> list:
        """获取所有结果"""
        return list(self._results.values())
    
    def get_results_by_data(self, data_id: int) -> list:
        """获取指定数据的所有结果"""
        return [r for r in self._results.values() if r.data_id == data_id]
    
    def clear(self):
        """清空所有结果"""
        self._results.clear()
        self._next_id = 1

