"""
测试JSON数据合并Base+Combine+Dissociation后的拟合
"""
import json
import pandas as pd
import numpy as np
import tempfile
import os

# 找JSON文件
json_files = [f for f in os.listdir('.') if f.endswith('.json')]
if not json_files:
    print("No JSON files")
    exit(1)

json_file = json_files[0]
print(f"="*70)
print(f"Test JSON with merged data: {json_file}")
print(f"="*70)

# 加载JSON
with open(json_file, encoding='utf-8') as f:
    json_data = json.load(f)

samples = json_data.get('CalculateDataList', [])
print(f"\nSamples: {len(samples)}")

# ⭐ 合并所有数据点的函数（复制自data_model.py）
def get_all_data_from_sample(sample):
    """Merge all data points"""
    all_data = []
    if 'BaseData' in sample and sample['BaseData']:
        all_data.extend(sample['BaseData'])
    if 'CombineData' in sample and sample['CombineData']:
        all_data.extend(sample['CombineData'])
    if 'DissociationData' in sample and sample['DissociationData']:
        all_data.extend(sample['DissociationData'])
    return all_data

# 获取第一个样本的所有数据
first_all_data = get_all_data_from_sample(samples[0])
print(f"\nFirst sample data points:")
print(f"  BaseData: {len(samples[0].get('BaseData', []))}")
print(f"  CombineData: {len(samples[0].get('CombineData', []))}")
print(f"  DissociationData: {len(samples[0].get('DissociationData', []))}")
print(f"  Total: {len(first_all_data)}")

# 提取时间
time_values = [d.get('XValue', 0) for d in first_all_data]
print(f"\nTime range: {min(time_values)} ~ {max(time_values)}")

# 构建宽表
wide_data = {'Time': time_values}

for i, sample in enumerate(samples):
    conc = sample.get('Concentration', 0.0)
    all_data = get_all_data_from_sample(sample)
    y_vals = [d.get('YValue', 0.0) for d in all_data]
    wide_data[str(conc)] = y_vals
    print(f"  Sample {i+1}: conc={conc}, points={len(y_vals)}")

df = pd.DataFrame(wide_data)
print(f"\nWide DataFrame:")
print(f"  Shape: {df.shape}")
print(f"  Columns: {list(df.columns)}")
print(f"\nFirst 10 rows:")
print(df.head(10))
print(f"\nLast 5 rows:")
print(df.tail(5))

# 保存并拟合
with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
    tmp_path = tmp.name

try:
    df.to_excel(tmp_path, index=False)
    print(f"\nTemp Excel: {tmp_path}")
    
    # 调用model_runner
    import sys
    sys.path.insert(0, '.')
    from model_data_process.LocalBivariate import model_runner
    
    print("\n" + "="*70)
    print("Calling model_runner...")
    print("="*70)
    
    result = model_runner(tmp_path)
    
    print("="*70)
    print("model_runner returned")
    print("="*70)
    
    if result and isinstance(result, dict):
        T_data = result.get('T_data')
        Y_data = result.get('Y_data')
        Y_pred = result.get('Y_pred')
        params = result.get('parameters', {})
        
        print(f"\nResult shapes:")
        print(f"  T_data: {T_data.shape}")
        print(f"  Y_data: {Y_data.shape}")
        print(f"  Y_pred: {Y_pred.shape}")
        
        print(f"\nFitting parameters:")
        print(f"  Rmax: {params.get('Rmax', 'N/A'):.2f} RU")
        print(f"  kon: {params.get('kon', 'N/A'):.4e} 1/(M*s)")
        print(f"  koff: {params.get('koff', 'N/A'):.4e} 1/s")
        print(f"  KD: {params.get('KD', 'N/A'):.4e} M")
        
        # 统计
        Y_flat = Y_pred.flatten()
        Y_data_flat = Y_data.flatten()
        
        print(f"\nY_data statistics:")
        print(f"  Min: {np.min(Y_data_flat):.2f}")
        print(f"  Max: {np.max(Y_data_flat):.2f}")
        print(f"  Mean: {np.mean(Y_data_flat):.2f}")
        
        print(f"\nY_pred statistics:")
        print(f"  Min: {np.min(Y_flat):.2f}")
        print(f"  Max: {np.max(Y_flat):.2f}")
        print(f"  Mean: {np.mean(Y_flat):.2f}")
        print(f"  Std: {np.std(Y_flat):.2f}")
        
        # R²
        if np.std(Y_flat) > 1e-10:
            residuals = Y_pred.flatten() - Y_data_flat
            rmse = np.sqrt(np.mean(residuals**2))
            ss_tot = np.sum((Y_data_flat - np.mean(Y_data_flat))**2)
            ss_res = np.sum(residuals**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            print(f"\nRMSE: {rmse:.2f}")
            print(f"R-squared: {r2:.4f}")
            
            if r2 > 0.9:
                print(f"\n[SUCCESS] Excellent fitting! (R^2 > 0.9)")
            elif r2 > 0.5:
                print(f"\n[OK] Good fitting (R^2 > 0.5)")
            elif r2 > 0:
                print(f"\n[Warning] Moderate fitting (0 < R^2 < 0.5)")
            else:
                print(f"\n[ERROR] Poor fitting (R^2 < 0)")
        else:
            print(f"\n[ERROR] Y_pred is constant!")
    else:
        print(f"\n[ERROR] model_runner returned wrong format: {type(result)}")

finally:
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
        print(f"\nCleaned up temp file")

