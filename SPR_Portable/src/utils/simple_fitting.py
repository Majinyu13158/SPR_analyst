"""
简化版拟合 - 直接参考旧项目的简单粗暴方式
跳过智能XY提取，直接处理数据
"""
import pandas as pd
import numpy as np
import tempfile
import os
from typing import Dict, Any


def simple_local_bivariate_fit(data) -> Dict[str, Any]:
    """
    简化版LocalBivariate拟合
    
    参数:
        data: Data对象，包含dataframe
    
    返回:
        拟合结果字典
    """
    try:
        df = data.dataframe
        
        if df is None or df.empty:
            return {
                'success': False,
                'error': '数据为空'
            }
        
        print(f"[SimpleFitting] DataFrame形状: {df.shape}")
        print(f"[SimpleFitting] 列名: {list(df.columns)}")
        print(f"[SimpleFitting] 前5行:")
        print(df.head())
        
        # ⭐ 检查DataFrame格式
        # 期望格式：Time | 浓度1 | 浓度2 | ... | 浓度N
        # 列名：Time, 0.0, 1.0e-9, 2.0e-9, ...
        
        cols = list(df.columns)
        if len(cols) < 2:
            return {
                'success': False,
                'error': f'列数不足，至少需要2列（Time + 1个浓度），实际: {len(cols)}'
            }
        
        # 检查第一列是否是Time
        first_col = cols[0]
        if first_col not in ['Time', 'time', 'XValue', 'X']:
            return {
                'success': False,
                'error': f'第一列应该是Time，实际: {first_col}'
            }
        
        # 检查其他列是否是数值（浓度）
        conc_cols = cols[1:]
        try:
            concentrations = [float(str(col)) for col in conc_cols]
            print(f"[SimpleFitting] ✅ 浓度列: {concentrations}")
        except (ValueError, TypeError) as e:
            return {
                'success': False,
                'error': f'列名不是数值（浓度），列名: {conc_cols}, 错误: {e}'
            }
        
        # ⭐ 直接保存为Excel，调用原始model_runner
        # 这是旧项目的"简单粗暴"方式
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # 保存DataFrame为Excel（保持原始格式）
            df.to_excel(tmp_path, index=False)
            print(f"[SimpleFitting] ✅ 临时Excel: {tmp_path}")
            print(f"[SimpleFitting] Excel形状: {df.shape}")
            
            # 调用原始model_runner
            from model_data_process.LocalBivariate import model_runner
            print(f"[SimpleFitting] 调用model_runner...")
            print("="*70)
            
            result = model_runner(tmp_path)
            
            print("="*70)
            print(f"[SimpleFitting] model_runner返回完成")
            
            # 解析结果
            if result and len(result) == 3:
                T_data, Y_data, Y_pred = result
                
                print(f"[SimpleFitting] 返回值形状:")
                print(f"  T_data: {T_data.shape if hasattr(T_data, 'shape') else type(T_data)}")
                print(f"  Y_data: {Y_data.shape if hasattr(Y_data, 'shape') else type(Y_data)}")
                print(f"  Y_pred: {Y_pred.shape if hasattr(Y_pred, 'shape') else type(Y_pred)}")
                
                # 检查Y_pred是否全是0或常数
                if hasattr(Y_pred, 'flatten'):
                    Y_flat = Y_pred.flatten()
                    print(f"  Y_pred统计: min={np.min(Y_flat):.6e}, max={np.max(Y_flat):.6e}, std={np.std(Y_flat):.6e}")
                    
                    if np.std(Y_flat) < 1e-10:
                        print(f"[SimpleFitting] ⚠️ 警告：Y_pred是常数（标准差接近0）")
                
                # 提取参数（从控制台输出中已经打印了Rmax, kon, koff, KD）
                # 这里只能返回占位值，因为model_runner没有返回参数
                
                return {
                    'success': True,
                    'parameters': {
                        'Rmax': (np.nan, None, 'RU'),
                        'kon': (np.nan, None, '1/(M*s)'),
                        'koff': (np.nan, None, '1/s'),
                        'KD': (np.nan, None, 'M')
                    },
                    'y_pred': Y_pred.flatten() if hasattr(Y_pred, 'ndim') and Y_pred.ndim > 1 else Y_pred,
                    'statistics': {
                        'chi2': None,
                        'r2': None,
                        'rmse': None
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
                print(f"[SimpleFitting] 清理临时文件: {tmp_path}")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'拟合过程出错: {str(e)}'
        }


def test_simple_fit():
    """测试简化拟合"""
    import sys
    sys.path.insert(0, '.')
    
    # 加载JSON数据
    import json
    json_files = [x for x in os.listdir('.') if x.endswith('.json')]
    if not json_files:
        print("找不到JSON文件")
        return
    
    json_file = json_files[0]
    print(f"加载JSON: {json_file}")
    
    with open(json_file, encoding='utf-8') as f:
        json_data = json.load(f)
    
    # 创建Data对象
    from src.models.data_model import Data
    data = Data(item=json_data, itemtype='file')
    
    print(f"\n数据名称: {data.name}")
    print(f"DataFrame形状: {data.dataframe.shape}")
    print(f"DataFrame列名: {list(data.dataframe.columns)}")
    
    # 执行拟合
    print("\n" + "="*70)
    print("开始拟合...")
    print("="*70)
    
    result = simple_local_bivariate_fit(data)
    
    print("\n" + "="*70)
    print("拟合结果:")
    print("="*70)
    print(f"成功: {result['success']}")
    if result['success']:
        print(f"参数: {result['parameters']}")
        y_pred = result['y_pred']
        print(f"Y预测形状: {y_pred.shape if hasattr(y_pred, 'shape') else type(y_pred)}")
        if hasattr(y_pred, '__len__') and len(y_pred) > 0:
            print(f"Y预测前5个值: {y_pred[:5]}")
    else:
        print(f"错误: {result['error']}")


if __name__ == '__main__':
    test_simple_fit()

