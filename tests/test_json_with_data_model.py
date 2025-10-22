"""
使用修复后的Data类测试JSON拟合
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import tempfile
import numpy as np

# 避免PySide6依赖
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from src.models.data_model import Data

# 找JSON文件
json_files = [f for f in os.listdir('.') if f.endswith('.json')]
if not json_files:
    print("No JSON files")
    exit(1)

json_file = json_files[0]
print(f"="*70)
print(f"Test JSON fitting with Data model: {json_file}")
print(f"="*70)

# 加载JSON
with open(json_file, encoding='utf-8') as f:
    json_data = json.load(f)

print(f"\n[Step 1] Create Data object from JSON...")

# 使用Data类加载（会自动合并Base+Combine+Dissociation）
data = Data(item=json_data, itemtype='file')

print(f"\n[Step 2] Check DataFrame...")
df = data.dataframe

if df is None or df.empty:
    print("ERROR: DataFrame is empty!")
    exit(1)

print(f"  Shape: {df.shape}")
print(f"  Columns: {list(df.columns)}")
print(f"\nFirst 10 rows:")
print(df.head(10))

# 保存为Excel并拟合
print(f"\n[Step 3] Save to Excel and fit...")

with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
    tmp_path = tmp.name

try:
    df.to_excel(tmp_path, index=False)
    print(f"Temp Excel: {tmp_path}")
    
    # 调用model_runner
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
        print(f"  Rmax: {params.get('Rmax', 'N/A'):.4f} RU")
        print(f"  kon: {params.get('kon', 'N/A'):.4e} 1/(M*s)")
        print(f"  koff: {params.get('koff', 'N/A'):.4e} 1/s")
        print(f"  KD: {params.get('KD', 'N/A'):.4e} M")
        
        # 统计
        Y_flat = Y_pred.flatten()
        Y_data_flat = Y_data.flatten()
        
        print(f"\nY_data statistics:")
        print(f"  Min: {np.min(Y_data_flat):.4f}")
        print(f"  Max: {np.max(Y_data_flat):.4f}")
        print(f"  Mean: {np.mean(Y_data_flat):.4f}")
        
        print(f"\nY_pred statistics:")
        print(f"  Min: {np.min(Y_flat):.4f}")
        print(f"  Max: {np.max(Y_flat):.4f}")
        print(f"  Mean: {np.mean(Y_flat):.4f}")
        print(f"  Std: {np.std(Y_flat):.4f}")
        
        # R²
        if np.std(Y_flat) > 1e-10:
            residuals = Y_pred.flatten() - Y_data_flat
            rmse = np.sqrt(np.mean(residuals**2))
            ss_tot = np.sum((Y_data_flat - np.mean(Y_data_flat))**2)
            ss_res = np.sum(residuals**2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            print(f"\nRMSE: {rmse:.4f}")
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

