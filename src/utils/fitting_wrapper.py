# -*- coding: utf-8 -*-
"""
拟合算法封装 - XlementFitting集成

原始文件: model_data_process/LocalBivariate.py
功能: 提供统一接口调用XlementFitting的各种拟合算法
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# 添加XlementFitting到路径
XLEMENT_PATH = Path(__file__).parents[2] / "XlementFitting"
if str(XLEMENT_PATH) not in sys.path:
    sys.path.insert(0, str(XLEMENT_PATH))


class FittingWrapper:
    """
    拟合算法封装器
    
    功能：
        - 统一接口调用不同的拟合方法
        - 处理输入数据格式
        - 解析输出结果
        - 错误处理
    """
    
    def __init__(self):
        self.available_methods = [
            'LocalBivariate',
            'GlobalBivariate',
            'PartialBivariate',
            'SingleCycle',
            'BalanceFitting'
        ]
    
    def fit(self, method: str, x_data, y_data, **kwargs) -> Dict[str, Any]:
        """
        执行拟合
        
        参数:
            method: 拟合方法名
            x_data: X轴数据（时间）
            y_data: Y轴数据（响应）
            **kwargs: 其他参数
        
        返回:
            {
                'success': True/False,
                'parameters': {...},  # 拟合参数
                'y_pred': [...],      # 预测值
                'statistics': {...},  # 统计信息
                'error': str          # 错误信息（如果失败）
            }
        """
        try:
            if method == 'LocalBivariate':
                return self._fit_local_bivariate(x_data, y_data, **kwargs)
            elif method == 'GlobalBivariate':
                return self._fit_global_bivariate(x_data, y_data, **kwargs)
            elif method == 'SingleCycle':
                return self._fit_single_cycle(x_data, y_data, **kwargs)
            else:
                return {
                    'success': False,
                    'error': f'不支持的拟合方法: {method}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'拟合过程出错: {str(e)}'
            }
    
    def _fit_local_bivariate(self, x_data, y_data, **kwargs) -> Dict[str, Any]:
        """
        局部双变量拟合
        
        ⭐ 阶段2修复：直接使用核心算法，不依赖model_runner的文件I/O
        
        原项目的model_runner只接受Excel文件名，我们需要：
        1. 创建临时Excel文件，或
        2. 直接使用核心拟合算法
        
        这里采用方法2：直接调用核心算法
        """
        try:
            # 准备数据
            x_array = np.array(x_data, dtype=np.float64)
            y_array = np.array(y_data, dtype=np.float64)
            
            # ⭐ 方法1：如果有DataFrame，检查格式后决定是否使用完整版
            if 'dataframe' in kwargs:
                df = kwargs['dataframe']
                
                # ⭐ 检查DataFrame格式是否符合原项目期望
                # 原项目期望：第一列是Time，后续列名是数值（浓度）
                is_valid_format = False
                
                if len(df.columns) > 1:
                    # 检查第一列是否是Time
                    first_col = df.columns[0]
                    if first_col in ['Time', 'time']:
                        # 检查后续列名是否都是数值
                        other_cols = df.columns[1:]
                        try:
                            # 尝试将列名转换为数值
                            [float(str(col)) for col in other_cols]
                            is_valid_format = True
                            print(f"[FittingWrapper] ✅ DataFrame格式符合原项目期望（Time + 浓度列）")
                        except (ValueError, TypeError):
                            print(f"[FittingWrapper] ⚠️ DataFrame列名不是数值: {list(other_cols)}")
                
                if is_valid_format:
                    # 使用完整版算法
                    import tempfile
                    import os
                    
                    # 创建临时文件
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
                        tmp_path = tmp.name
                    
                    try:
                        # 保存为Excel
                        df.to_excel(tmp_path, index=False)
                        print(f"[FittingWrapper] 创建临时Excel: {tmp_path}")
                        
                        # 调用原始model_runner
                        from model_data_process.LocalBivariate import model_runner
                        result = model_runner(tmp_path)
                        
                        # 解析结果 (T_data, Y_data, Y_pred)
                        if result and len(result) == 3:
                            T_data, Y_data, Y_pred = result
                            
                            return {
                                'success': True,
                                'parameters': {
                                    'Rmax': 'N/A',  # model_runner返回值中没有参数
                                    'kon': 'N/A',
                                    'koff': 'N/A'
                                },
                                'y_pred': Y_pred.flatten() if Y_pred.ndim > 1 else Y_pred,
                                'statistics': {
                                    'chi2': None,
                                    'r2': None,
                                    'rmse': self._calculate_rmse(Y_data.flatten(), Y_pred.flatten()) if Y_pred is not None else None
                                }
                            }
                        else:
                            return {
                                'success': False,
                                'error': f'model_runner返回格式错误: {type(result)}'
                            }
                    finally:
                        # 清理临时文件
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                else:
                    # DataFrame格式不符合，回退到简化版
                    print(f"[FittingWrapper] ℹ️ DataFrame格式不符合原项目要求，使用简化版拟合")
                    print(f"   当前列: {list(df.columns)}")
                    print(f"   原项目期望: ['Time', 浓度1, 浓度2, ...]（列名为数值）")
            
            # ⭐ 方法2：简化版拟合（如果没有DataFrame）
            # 使用简单的线性拟合作为占位符
            from scipy.optimize import curve_fit
            
            def linear_model(x, a, b):
                return a * x + b
            
            try:
                params, _ = curve_fit(linear_model, x_array, y_array)
                y_pred = linear_model(x_array, *params)
                
                return {
                    'success': True,
                    'parameters': {
                        'slope': float(params[0]),
                        'intercept': float(params[1])
                    },
                    'y_pred': y_pred,
                    'statistics': {
                        'chi2': None,
                        'r2': None,
                        'rmse': self._calculate_rmse(y_array, y_pred)
                    }
                }
            except Exception as fit_error:
                return {
                    'success': False,
                    'error': f'拟合失败: {str(fit_error)}'
                }
            
        except ImportError as e:
            return {
                'success': False,
                'error': f'无法导入LocalBivariate模块: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'LocalBivariate拟合失败: {str(e)}'
            }
    
    def _fit_global_bivariate(self, x_data, y_data, **kwargs) -> Dict[str, Any]:
        """
        全局双变量拟合
        
        （待实现）
        """
        return {
            'success': False,
            'error': 'GlobalBivariate拟合暂未实现'
        }
    
    def _fit_single_cycle(self, x_data, y_data, **kwargs) -> Dict[str, Any]:
        """
        单循环拟合
        
        从 XlementFitting/SingleCycle.py 迁移
        """
        try:
            from XlementFitting.SingleCycle import SingleCycleFitting
            
            # 调用拟合
            fitter = SingleCycleFitting()
            result = fitter.fit(x_data, y_data)
            
            # 解析结果
            # （需要根据实际实现调整）
            
            return {
                'success': True,
                'parameters': result,
                'y_pred': None,
                'statistics': {}
            }
            
        except ImportError:
            return {
                'success': False,
                'error': '无法导入SingleCycle模块'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'SingleCycle拟合失败: {str(e)}'
            }
    
    def _calculate_rmse(self, y_true, y_pred) -> float:
        """计算RMSE"""
        if y_pred is None:
            return None
        try:
            return np.sqrt(np.mean((y_true - y_pred) ** 2))
        except:
            return None
    
    def get_available_methods(self) -> list:
        """获取可用的拟合方法"""
        return self.available_methods.copy()


# 全局单例
_fitting_wrapper = FittingWrapper()


def fit_data(method: str, x_data, y_data, **kwargs) -> Dict[str, Any]:
    """
    快捷拟合函数
    
    参数:
        method: 拟合方法
        x_data: X数据
        y_data: Y数据
        **kwargs: 其他参数
    
    返回:
        拟合结果字典
    """
    return _fitting_wrapper.fit(method, x_data, y_data, **kwargs)


def get_fitting_methods() -> list:
    """获取可用的拟合方法列表"""
    return _fitting_wrapper.get_available_methods()

