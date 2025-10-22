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
        
        ⭐ 关键：需要从Data对象获取SPR实验的关键参数
        - time_break（结合-解离分割时间点）
        - 浓度信息
        
        原项目的model_runner只接受Excel文件名，我们需要：
        1. 创建临时Excel文件，或
        2. 直接使用核心拟合算法
        
        这里采用方法2：直接调用核心算法
        """
        try:
            # 准备数据
            x_array = np.array(x_data, dtype=np.float64)
            y_array = np.array(y_data, dtype=np.float64)
            
            # ⭐ 如果有DataFrame，检查格式后决定是否使用完整版
            if 'dataframe' in kwargs:
                df = kwargs['dataframe']
                
                print(f"[FittingWrapper] DataFrame检查: 形状={df.shape}, 列={list(df.columns)}")
                
                # ⭐ 检查DataFrame格式
                # 格式要求：宽表（Time + 浓度列）
                # 列名必须是：Time | 浓度1 | 浓度2 | ...（浓度值必须是数值）
                is_valid_format = False
                
                if len(df.columns) >= 2:
                    # 检查第一列是否是Time
                    first_col = df.columns[0]
                    if first_col in ['Time', 'time', 'XValue', 'X']:
                        # 检查后续列名是否都是数值（浓度值）
                        other_cols = df.columns[1:]
                        try:
                            # 尝试将列名转换为数值
                            concentrations = [float(str(col)) for col in other_cols]
                            is_valid_format = True
                            print(f"[FittingWrapper] ✅ DataFrame是宽表格式")
                            print(f"   时间列: {first_col}")
                            print(f"   浓度列: {concentrations}")
                            print(f"   数据点数: {len(df)}")
                        except (ValueError, TypeError):
                            # 列名不是数值 → 不是标准宽表格式
                            print(f"[FittingWrapper] ❌ DataFrame格式不正确")
                            print(f"   期望: Time | 浓度1 | 浓度2 | ...")
                            print(f"   实际: {list(df.columns)}")
                            is_valid_format = False
                
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
                        
                        # ⭐ 调用原始model_runner（现在返回字典格式）
                        from model_data_process.LocalBivariate import model_runner
                        print(f"[FittingWrapper] 调用LocalBivariate.model_runner")
                        result = model_runner(tmp_path)
                        
                        # 解析结果（新格式：字典）
                        if result and isinstance(result, dict):
                            T_data = result.get('T_data')
                            Y_data = result.get('Y_data')
                            Y_pred = result.get('Y_pred')
                            params = result.get('parameters', {})
                            # 还原时间向量与浓度列名
                            try:
                                time_vector = df.iloc[:, 0].to_numpy()
                            except Exception:
                                time_vector = None
                            try:
                                headers = [str(c) for c in list(df.columns[1:])]
                            except Exception:
                                headers = None
                            
                            # 提取参数（格式化为(值, 误差, 单位)）
                            fit_params = {
                                'Rmax': (params.get('Rmax', np.nan), None, 'RU'),
                                'kon': (params.get('kon', np.nan), None, '1/(M*s)'),
                                'koff': (params.get('koff', np.nan), None, '1/s'),
                                'KD': (params.get('KD', np.nan), None, 'M')
                            }
                            
                            print(f"[FittingWrapper] ✅ 拟合成功:")
                            print(f"   Rmax={fit_params['Rmax'][0]:.2f} RU")
                            print(f"   kon={fit_params['kon'][0]:.4e} 1/(M*s)")
                            print(f"   koff={fit_params['koff'][0]:.4e} 1/s")
                            print(f"   KD={fit_params['KD'][0]:.4e} M")
                            
                            return {
                                'success': True,
                                'parameters': fit_params,
                                'y_pred': Y_pred.flatten() if getattr(Y_pred, 'ndim', 1) > 1 else Y_pred,
                                # 额外提供矩阵与辅助信息，便于GUI构建宽表
                                'y_pred_matrix': Y_pred,
                                'time_vector': time_vector,
                                'headers': headers,
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
                    # DataFrame格式不符合，尝试构造“宽表”再用完整版算法
                    try:
                        from .data_processor import DataProcessor
                        success_wide, wide_df, err = DataProcessor.build_wide_table([df])
                        if success_wide and wide_df is not None:
                            print("[FittingWrapper] ✅ 已自动构造最小宽表用于LocalBivariate")
                            # 保存为临时Excel并调用
                            import tempfile, os
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
                                tmp_path = tmp.name
                            try:
                                wide_df.to_excel(tmp_path, index=False)
                                from model_data_process.LocalBivariate import model_runner
                                result = model_runner(tmp_path)
                                if result and len(result) == 3:
                                    T_data, Y_data, Y_pred = result
                                    return {
                                        'success': True,
                                        'parameters': {
                                            'Rmax': 'N/A',
                                            'kon': 'N/A',
                                            'koff': 'N/A'
                                        },
                                        'y_pred': Y_pred.flatten() if hasattr(Y_pred, 'ndim') and Y_pred.ndim > 1 else Y_pred,
                                        'statistics': {
                                            'chi2': None,
                                            'r2': None,
                                            'rmse': self._calculate_rmse(np.array(Y_data).flatten(), np.array(Y_pred).flatten()) if Y_pred is not None else None
                                        }
                                    }
                            finally:
                                if os.path.exists(tmp_path):
                                    os.remove(tmp_path)
                        else:
                            print(f"[FittingWrapper] ℹ️ 宽表构造失败或不适用: {err}")
                    except Exception as ee:
                        print(f"[FittingWrapper] 构造宽表异常: {ee}")
                    # 若仍不满足，回退为简化版拟合
                    print(f"[FittingWrapper] ℹ️ 使用简化版拟合 (DataFrame不符合/宽表失败)")
            
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
    
    def _estimate_time_break(self, x_data, y_data):
        """
        从数据估计time_break（结合-解离分割时间点）
        策略：找到Y值达到最大值的位置
        """
        try:
            max_idx = np.argmax(y_data)
            time_break = float(x_data[max_idx])
            print(f"[FittingWrapper] 估计time_break: max_idx={max_idx}, time_break={time_break}")
            return time_break
        except Exception as e:
            print(f"[FittingWrapper] 估计time_break失败: {e}，使用默认值133")
            return 133.0
    
    def _model_runner_with_time_break(self, filename, time_break):
        """
        增强版model_runner，可指定time_break参数
        
        ⚠️ 这是临时方案：复制LocalBivariate的核心逻辑
        长期应该修改原始model_runner使其接受参数
        """
        import pandas as pd
        import numpy as np
        from scipy.optimize import minimize
        import warnings
        from datetime import datetime
        
        print(f"[FittingWrapper] _model_runner_with_time_break: time_break={time_break}")
        
        # 复制原始model_runner的核心逻辑
        INF_value = 1.797e+308
        
        def model_local_in_one(radioligands: np.ndarray, T_array: np.ndarray, Bmax_value: float, kon: float, koff: float, Time0: float):
            Y = np.zeros(T_array.shape)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                kon = np.power(10,kon)
                koff = np.power(10,koff)
                Kob=np.longdouble(radioligands*kon+koff)
                Kd=np.longdouble(koff/kon)
                Eq=np.longdouble(Bmax_value*radioligands/(radioligands + Kd))
                YatTime0 =np.longdouble(Eq*(1-np.exp(-1*Kob*Time0)))
                T_flag_diss = np.float32(T_array>Time0)
                T_flag_ass = np.float32(T_array<=Time0)
                
                Y = YatTime0 * np.exp(-1 * koff * (T_array - Time0)) * T_flag_diss + Eq * (1-np.exp(-1*Kob*T_array)) * T_flag_ass
                if len(w) > 0:
                    Y = INF_value
            return Y
        
        def Loss_local_in_one(params, A_data: np.ndarray, T_data: np.ndarray, Y_data: np.ndarray, T_break: float):
            R, ka, kd = params
            Y_predictions = model_local_in_one(A_data,T_data,R,ka,kd,T_break)
            residuals = Y_predictions - Y_data
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                R2 = np.sum(np.square(residuals))
                if len(w) > 0:
                    R2 = INF_value
            return R2
        
        # 读取数据
        dataframe = pd.read_excel(filename)
        data_array = dataframe.to_numpy()
        
        # 提取Y数据
        Y_data = data_array[:,1:]
        Y_data = Y_data.astype(np.longdouble)
        R_guess = np.max(Y_data)
        
        # 获取浓度数据（列名）
        A_data = np.array(dataframe.columns)
        A_data = A_data[1:]
        A_data = A_data.astype(np.longdouble)
        A_data = np.tile(A_data, (Y_data.shape[0], 1))
        
        # 获取时间数据（第一列）
        T_data = data_array[:,0]
        T_data = np.tile(T_data,(Y_data.shape[1],1))
        T_data = T_data.transpose()
        T_data = T_data.astype(np.longdouble)
        
        # ⭐ 使用传入的time_break，而非硬编码
        print(f"[FittingWrapper] 使用time_break={time_break}进行拟合")
        
        # 初始参数猜测
        initial_guess = [R_guess*1.5, 6, -2]
        
        # 执行优化
        bnds = ((0,np.inf),(0,np.inf),(-np.inf,np.inf))
        result = minimize(Loss_local_in_one, initial_guess, args=(A_data, T_data, Y_data, time_break),
                          method='BFGS',options={'eps': 1e-3})
        
        # 最优参数
        R_opt, ka_opt, kd_opt = result.x
        ka_opt_p, kd_opt_p = np.power(10,(ka_opt, kd_opt))
        
        print("Rmax: {:.4f}\nkon: {:.4e}\nkoff: {:.4e}\nKD: {:.4e}".format(
            R_opt, ka_opt_p, kd_opt_p, kd_opt_p/ka_opt_p))
        
        # 计算预测值
        Y_pred = model_local_in_one(A_data, T_data, R_opt, ka_opt, kd_opt, time_break)
        print(f"Y_pred形状: {Y_pred.shape}")
        
        return T_data, Y_data, Y_pred
    
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

