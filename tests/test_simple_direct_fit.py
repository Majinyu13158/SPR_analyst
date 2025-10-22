"""
直接测试拟合 - 不依赖GUI
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pandas as pd
import numpy as np
import tempfile


def test_direct_fit():
    """直接测试拟合流程"""
    
    # 找到JSON文件
    json_files = [x for x in os.listdir('.') if x.endswith('.json')]
    if not json_files:
        print("找不到JSON文件")
        return
    
    json_file = json_files[0]
    print(f"加载JSON: {json_file}")
    
    with open(json_file, encoding='utf-8') as f:
        json_data = json.load(f)
    
    # 手动构建宽表（模拟data_model的_build_wide_table_from_samples）
    samples = json_data['CalculateDataList']
    print(f"\n样本数: {len(samples)}")
    
    # 提取时间点
    first_base_data = samples[0].get('BaseData', [])
    time_values = [d.get('XValue', d.get('Time', 0)) for d in first_base_data]
    
    # 构建宽表
    wide_data = {'Time': time_values}
    
    for sample in samples:
        concentration = sample.get('Concentration', 0.0)
        base_data = sample.get('BaseData', [])
        y_values = [d.get('YValue', 0.0) for d in base_data]
        wide_data[str(concentration)] = y_values
    
    df = pd.DataFrame(wide_data)
    
    print(f"\n宽表DataFrame:")
    print(f"形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
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
        
        if result and len(result) == 3:
            T_data, Y_data, Y_pred = result
            
            print(f"\n返回值:")
            print(f"  T_data形状: {T_data.shape}")
            print(f"  Y_data形状: {Y_data.shape}")
            print(f"  Y_pred形状: {Y_pred.shape}")
            
            print(f"\n  T_data前5行:")
            print(T_data[:5])
            
            print(f"\n  Y_data前5行:")
            print(Y_data[:5])
            
            print(f"\n  Y_pred前5行:")
            print(Y_pred[:5])
            
            # 统计
            Y_flat = Y_pred.flatten()
            print(f"\nY_pred统计:")
            print(f"  最小值: {np.min(Y_flat):.6e}")
            print(f"  最大值: {np.max(Y_flat):.6e}")
            print(f"  平均值: {np.mean(Y_flat):.6e}")
            print(f"  标准差: {np.std(Y_flat):.6e}")
            
            # 检查是否是常数
            if np.std(Y_flat) < 1e-10:
                print(f"\n⚠️ 警告：Y_pred是常数！")
            else:
                print(f"\n✅ Y_pred不是常数，拟合可能成功")
                
                # 检查与原始数据的拟合程度
                Y_data_flat = Y_data.flatten()
                residuals = Y_pred.flatten() - Y_data_flat
                rmse = np.sqrt(np.mean(residuals**2))
                print(f"\nRMSE: {rmse:.6e}")
            
        else:
            print(f"\n❌ model_runner返回格式错误: {type(result)}")
    
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            print(f"\n清理临时文件")


if __name__ == '__main__':
    test_direct_fit()

