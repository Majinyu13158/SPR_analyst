"""
用旧项目的Excel数据测试拟合
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
import tempfile

print("="*70)
print("加载旧项目Excel数据并测试拟合")
print("="*70)

# 查找Excel文件
excel_file = None
for f in os.listdir('.'):
    if f.endswith('.xlsx') and '150KD' in f:
        excel_file = f
        break

if not excel_file:
    print("找不到Excel文件")
    exit(1)

print(f"\n加载Excel: {excel_file}")

# 读取数据
df_orig = pd.read_excel(excel_file)
print(f"原始形状: {df_orig.shape}")
print(f"原始列名: {list(df_orig.columns)}")

# 处理数据：第一列是时间索引，需要重命名为Time
df = df_orig.copy()

# 重命名第一列为Time
cols = list(df.columns)
cols[0] = 'Time'
df.columns = cols

print(f"\n处理后列名: {list(df.columns)}")
print(f"\n前10行:")
print(df.head(10))

# 保存为临时Excel
with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
    tmp_path = tmp.name

try:
    df.to_excel(tmp_path, index=False)
    print(f"\n临时Excel: {tmp_path}")
    
    # 调用model_runner
    from model_data_process.LocalBivariate import model_runner
    print("\n" + "="*70)
    print("调用model_runner...")
    print("="*70)
    
    result = model_runner(tmp_path)
    
    print("="*70)
    print("model_runner返回完成")
    print("="*70)
    
    if result and isinstance(result, dict):
        T_data = result.get('T_data')
        Y_data = result.get('Y_data')
        Y_pred = result.get('Y_pred')
        params = result.get('parameters', {})
        
        print(f"\n返回值形状:")
        print(f"  T_data: {T_data.shape}")
        print(f"  Y_data: {Y_data.shape}")
        print(f"  Y_pred: {Y_pred.shape}")
        
        print(f"\n  T_data前10行第1列:")
        print(T_data[:10, 0])
        
        print(f"\n  Y_data前10行第1列（浓度3.33e-09）:")
        print(Y_data[:10, 0])
        
        print(f"\n  Y_pred前10行第1列:")
        print(Y_pred[:10, 0])
        
        # 统计
        Y_flat = Y_pred.flatten()
        Y_data_flat = Y_data.flatten()
        
        print(f"\nY_data统计:")
        print(f"  最小值: {np.min(Y_data_flat):.2f}")
        print(f"  最大值: {np.max(Y_data_flat):.2f}")
        print(f"  平均值: {np.mean(Y_data_flat):.2f}")
        
        print(f"\n拟合参数:")
        print(f"  Rmax: {params.get('Rmax', 'N/A'):.4f} RU")
        print(f"  kon: {params.get('kon', 'N/A'):.4e} 1/(M*s)")
        print(f"  koff: {params.get('koff', 'N/A'):.4e} 1/s")
        print(f"  KD: {params.get('KD', 'N/A'):.4e} M")
        
        print(f"\nY_pred统计:")
        print(f"  最小值: {np.min(Y_flat):.2f}")
        print(f"  最大值: {np.max(Y_flat):.2f}")
        print(f"  平均值: {np.mean(Y_flat):.2f}")
        print(f"  标准差: {np.std(Y_flat):.2f}")
        
        # 检查是否是常数
        if np.std(Y_flat) < 1e-10:
            print(f"\n[ERROR] Y_pred是常数！")
        else:
            print(f"\n[OK] Y_pred不是常数")
            
            # 计算RMSE
            residuals = Y_pred.flatten() - Y_data_flat
            rmse = np.sqrt(np.mean(residuals**2))
            print(f"\nRMSE: {rmse:.2f}")
            
            # 计算R²
            ss_tot = np.sum((Y_data_flat - np.mean(Y_data_flat))**2)
            ss_res = np.sum(residuals**2)
            r2 = 1 - (ss_res / ss_tot)
            print(f"R-squared: {r2:.4f}")
            
            if r2 > 0.5:
                print(f"\n[OK] Fitting quality is GOOD! (R^2 > 0.5)")
            else:
                print(f"\n[Warning] Fitting quality is poor (R^2 < 0.5)")
        
    else:
        print(f"\n[ERROR] model_runner返回格式错误: {type(result)}")

finally:
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
        print(f"\n清理临时文件")

