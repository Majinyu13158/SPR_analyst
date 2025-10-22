"""
测试model_runner的数据格式理解
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd

def test_localbivariate_data_format():
    """
    测试LocalBivariate期望的数据格式
    """
    print("\n" + "="*70)
    print("测试: LocalBivariate的数据格式")
    print("="*70)
    
    # 模拟Excel数据格式（宽表）
    # Time | 0.0 | 10.0 | 20.0  <- 列名是浓度
    # 0    | 0.5 | 1.2  | 2.3
    # 1    | 0.8 | 2.5  | 4.1
    # 2    | 1.0 | 3.0  | 5.0
    
    time_points = np.array([0, 1, 2, 3, 4])
    concentrations = [0.0, 10.0, 20.0]
    
    # 创建DataFrame
    df_data = {
        'Time': time_points,
        '0.0': [0.5, 0.8, 1.0, 0.9, 0.7],
        '10.0': [1.2, 2.5, 3.0, 2.5, 2.0],
        '20.0': [2.3, 4.1, 5.0, 4.5, 3.8]
    }
    df = pd.DataFrame(df_data)
    
    print("\n[1] 原始DataFrame（宽表格式）:")
    print(df)
    
    # 模拟LocalBivariate的数据提取
    data_array = df.to_numpy()
    print(f"\n[2] to_numpy()后: {data_array.shape}")
    print(data_array)
    
    # Y_data = data_array[:,1:]
    Y_data = data_array[:, 1:]
    print(f"\n[3] Y_data（所有列除了第一列）: {Y_data.shape}")
    print(Y_data)
    
    # A_data（浓度）
    A_data = np.array(df.columns)
    A_data = A_data[1:]
    print(f"\n[4] A_data（浓度，从列名提取）: {A_data.shape}")
    print(A_data)
    
    # A_data扩展
    A_data_tiled = np.tile(A_data.astype(float), (Y_data.shape[0], 1))
    print(f"\n[5] A_data扩展到每个时间点: {A_data_tiled.shape}")
    print(A_data_tiled)
    
    # T_data
    T_data = data_array[:, 0]
    print(f"\n[6] T_data（第一列）: {T_data.shape}")
    print(T_data)
    
    # T_data扩展
    T_data_tiled = np.tile(T_data, (Y_data.shape[1], 1))
    print(f"\n[7] T_data扩展: {T_data_tiled.shape}")
    print(T_data_tiled)
    
    T_data_final = T_data_tiled.transpose()
    print(f"\n[8] T_data转置后: {T_data_final.shape}")
    print(T_data_final)
    
    print("\n" + "="*70)
    print("关键发现:")
    print("="*70)
    print(f"- Y_data形状: {Y_data.shape} (n_time, n_concentration)")
    print(f"- A_data形状: {A_data_tiled.shape} (n_time, n_concentration)")
    print(f"- T_data形状: {T_data_final.shape} (n_time, n_concentration)")
    print("\n所有数据都是二维数组，每列代表一个浓度下的时间序列！")
    print("Y_pred应该也是同样的二维形状！")
    

def test_single_sample_vs_multi_concentration():
    """
    对比单样本数据和多浓度数据
    """
    print("\n" + "="*70)
    print("测试: 单样本 vs 多浓度数据")
    print("="*70)
    
    # 单样本数据（从JSON BaseData转换）
    print("\n[单样本格式] - 从JSON BaseData:")
    single_df = pd.DataFrame({
        'Time': [0, 1, 2, 3, 4],
        'YValue': [0.5, 1.2, 2.0, 1.8, 1.5]
    })
    print(single_df)
    print(f"形状: {single_df.shape}")
    print("这是一个时间序列，只有一条曲线")
    
    # 多浓度数据（原项目标准格式）
    print("\n[多浓度格式] - 原项目标准:")
    multi_df = pd.DataFrame({
        'Time': [0, 1, 2, 3, 4],
        '0.0': [0.5, 1.2, 2.0, 1.8, 1.5],
        '10.0': [1.0, 2.5, 4.0, 3.5, 3.0],
        '20.0': [1.5, 3.8, 6.0, 5.2, 4.5]
    })
    print(multi_df)
    print(f"形状: {multi_df.shape}")
    print("这是多条曲线，每列是一个浓度")
    
    print("\n" + "="*70)
    print("关键问题:")
    print("="*70)
    print("1. 我们的JSON数据是单样本格式（Time + YValue）")
    print("2. LocalBivariate期望多浓度格式（Time + 浓度1 + 浓度2 + ...）")
    print("3. 转换时需要确保返回的y_pred维度匹配输入的x_data")
    

def test_return_value_mismatch():
    """
    测试返回值维度不匹配问题
    """
    print("\n" + "="*70)
    print("测试: 返回值维度不匹配")
    print("="*70)
    
    # 输入给拟合函数的数据（从get_xy_data获取）
    x_data = np.array([0, 1, 2, 3, 4])  # 一维，5个点
    y_data = np.array([0.5, 1.2, 2.0, 1.8, 1.5])  # 一维，5个点
    
    print(f"\n[输入] x_data: {x_data.shape} = {x_data}")
    print(f"[输入] y_data: {y_data.shape} = {y_data}")
    
    # 但是LocalBivariate返回的是二维数组
    # 假设我们转换成了1列的宽表（Time + 0.0）
    Y_pred_2d = np.array([
        [0.48],
        [1.18],
        [1.95],
        [1.82],
        [1.52]
    ])
    
    print(f"\n[返回] Y_pred（二维）: {Y_pred_2d.shape}")
    print(Y_pred_2d)
    
    # 如果flatten
    Y_pred_flat = Y_pred_2d.flatten()
    print(f"\n[返回] Y_pred（flatten后）: {Y_pred_flat.shape}")
    print(Y_pred_flat)
    
    print(f"\n[匹配检查] x_data.shape == Y_pred_flat.shape: {x_data.shape == Y_pred_flat.shape}")
    
    print("\n" + "="*70)
    print("结论:")
    print("="*70)
    print("如果单样本转换为1列宽表，flatten后维度应该匹配！")
    print("但需要确认返回的Y_pred确实对应正确的浓度列")


if __name__ == '__main__':
    test_localbivariate_data_format()
    test_single_sample_vs_multi_concentration()
    test_return_value_mismatch()

