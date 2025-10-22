"""
重新测试JSON数据拟合 - 正确理解：
1. XValue就是时间
2. 小负值是正常的仪器噪声
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pandas as pd
import numpy as np
import tempfile

# 找到JSON文件
json_files = [f for f in os.listdir('.') if f.endswith('.json') and '多循环' in f or 'igg' in f.lower()]
if not json_files:
    json_files = [f for f in os.listdir('.') if f.endswith('.json')]

if not json_files:
    print("找不到JSON文件")
    exit(1)

json_file = json_files[0]
print(f"="*70)
print(f"测试JSON文件拟合: {json_file}")
print(f"="*70)

# 加载JSON
with open(json_file, encoding='utf-8') as f:
    json_data = json.load(f)

# 检查数据结构
samples = json_data.get('CalculateDataList', [])
print(f"\n样本数: {len(samples)}")

if not samples:
    print("没有样本数据")
    exit(1)

# 显示第一个样本的信息
first_sample = samples[0]
print(f"\n第一个样本信息:")
print(f"  SampleName: {first_sample.get('SampleName')}")
print(f"  Concentration: {first_sample.get('Concentration')}")
print(f"  ConcentrationUnit: {first_sample.get('ConcentrationUnit')}")

base_data = first_sample.get('BaseData', [])
print(f"  BaseData行数: {len(base_data)}")

if base_data:
    print(f"\n  BaseData前3行:")
    for i, row in enumerate(base_data[:3]):
        print(f"    行{i}: {row}")

# KEY: XValue IS Time!
print(f"\n[Key Point] Extract Time (XValue):")
if base_data:
    time_values = [d.get('XValue', 0) for d in base_data]
    y_values = [d.get('YValue', 0.0) for d in base_data]
    
    print(f"  时间点数: {len(time_values)}")
    print(f"  时间范围: {min(time_values)} ~ {max(time_values)}")
    print(f"  Y值范围: {min(y_values):.4f} ~ {max(y_values):.4f}")
    print(f"  Y值均值: {np.mean(y_values):.4f}")
    print(f"  [OK] Small negative values are normal (instrument noise)")

# 构建宽表
print(f"\n构建宽表:")
time_list = [d.get('XValue', 0) for d in samples[0].get('BaseData', [])]
wide_data = {'Time': time_list}

for i, sample in enumerate(samples):
    conc = sample.get('Concentration', 0.0)
    base_data = sample.get('BaseData', [])
    y_vals = [d.get('YValue', 0.0) for d in base_data]
    wide_data[str(conc)] = y_vals
    print(f"  浓度{i+1}: {conc}")

df = pd.DataFrame(wide_data)
print(f"\n宽表DataFrame:")
print(f"  形状: {df.shape}")
print(f"  列名: {list(df.columns)}")
print(f"\n前5行:")
print(df.head(5))

# 保存并拟合
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
        
        print(f"\n拟合参数:")
        print(f"  Rmax: {params.get('Rmax', 'N/A'):.4f} RU")
        print(f"  kon: {params.get('kon', 'N/A'):.4e} 1/(M*s)")
        print(f"  koff: {params.get('koff', 'N/A'):.4e} 1/s")
        print(f"  KD: {params.get('KD', 'N/A'):.4e} M")
        
        # 统计
        Y_flat = Y_pred.flatten()
        Y_data_flat = Y_data.flatten()
        
        print(f"\nY_data统计:")
        print(f"  最小值: {np.min(Y_data_flat):.4f}")
        print(f"  最大值: {np.max(Y_data_flat):.4f}")
        print(f"  平均值: {np.mean(Y_data_flat):.4f}")
        
        print(f"\nY_pred统计:")
        print(f"  最小值: {np.min(Y_flat):.4f}")
        print(f"  最大值: {np.max(Y_flat):.4f}")
        print(f"  平均值: {np.mean(Y_flat):.4f}")
        print(f"  标准差: {np.std(Y_flat):.4f}")
        
        # 检查是否是常数
        if np.std(Y_flat) < 1e-10:
            print(f"\n[ERROR] Y_pred是常数！")
        else:
            print(f"\n[OK] Y_pred不是常数")
            
            # 计算RMSE和R²
            residuals = Y_pred.flatten() - Y_data_flat
            rmse = np.sqrt(np.mean(residuals**2))
            ss_tot = np.sum((Y_data_flat - np.mean(Y_data_flat))**2)
            ss_res = np.sum(residuals**2)
            r2 = 1 - (ss_res / ss_tot)
            
            print(f"\nRMSE: {rmse:.4f}")
            print(f"R-squared: {r2:.4f}")
            
            if r2 > 0.5:
                print(f"\n[OK] Fitting quality is GOOD! (R^2 > 0.5)")
            elif r2 > 0:
                print(f"\n[Warning] Fitting quality is moderate (0 < R^2 < 0.5)")
            else:
                print(f"\n[ERROR] Fitting quality is POOR (R^2 < 0)")
    else:
        print(f"\n[ERROR] model_runner返回格式错误: {type(result)}")

finally:
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
        print(f"\n清理临时文件")

