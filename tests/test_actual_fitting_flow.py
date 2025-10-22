"""
实际测试拟合流程
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
import tempfile

# 测试LocalBivariate的实际调用
from model_data_process.LocalBivariate import model_runner

def test_localbivariate_with_single_column():
    """
    测试LocalBivariate处理单列数据的情况
    """
    print("\n" + "="*70)
    print("测试: LocalBivariate处理单列数据")
    print("="*70)
    
    # 创建单列宽表数据
    time_points = np.linspace(0, 200, 201)
    
    # 模拟SPR曲线
    # 0-100: 结合阶段
    association = 50 * (1 - np.exp(-0.05 * time_points[:101]))
    # 100-200: 解离阶段
    dissociation = association[-1] * np.exp(-0.03 * (time_points[101:] - 100))
    y_values = np.concatenate([association, dissociation])
    
    # 创建宽表：Time + 一个浓度列
    df = pd.DataFrame({
        'Time': time_points,
        '0.0': y_values  # 单浓度
    })
    
    print("\n[1] 输入DataFrame:")
    print(df.head(10))
    print(f"形状: {df.shape}")
    
    # 保存到临时Excel
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        df.to_excel(tmp_path, index=False)
        print(f"\n[2] Excel已保存: {tmp_path}")
        
        # 调用model_runner
        print("\n[3] 调用model_runner...")
        print("="*70)
        result = model_runner(tmp_path)
        print("="*70)
        
        # 检查返回值
        if result and len(result) == 3:
            T_data, Y_data, Y_pred = result
            
            print(f"\n[4] 返回值:")
            print(f"  - T_data形状: {T_data.shape}")
            print(f"  - Y_data形状: {Y_data.shape}")
            print(f"  - Y_pred形状: {Y_pred.shape}")
            
            print(f"\n[5] T_data（前5个）:")
            print(T_data[:5])
            
            print(f"\n[6] Y_data（前5个）:")
            print(Y_data[:5])
            
            print(f"\n[7] Y_pred（前5个）:")
            print(Y_pred[:5])
            
            # 如果是单列，应该是 (n, 1)
            if Y_pred.ndim == 2 and Y_pred.shape[1] == 1:
                print(f"\n[8] Y_pred是二维数组，形状 {Y_pred.shape}")
                print("  flatten后:")
                Y_pred_flat = Y_pred.flatten()
                print(f"  形状: {Y_pred_flat.shape}")
                print(f"  前5个值: {Y_pred_flat[:5]}")
                
                # 检查是否是直线
                is_constant = np.std(Y_pred_flat) < 0.1
                print(f"\n[9] 是否是常数/直线? {is_constant}")
                print(f"  标准差: {np.std(Y_pred_flat):.4f}")
                print(f"  最小值: {np.min(Y_pred_flat):.4f}")
                print(f"  最大值: {np.max(Y_pred_flat):.4f}")
            
            # 绘图对比
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 6))
            
            if Y_data.ndim == 2:
                plt.plot(T_data[:, 0], Y_data[:, 0], 'o-', label='Original', alpha=0.7)
                plt.plot(T_data[:, 0], Y_pred[:, 0], 's-', label='Fitted', alpha=0.7)
            else:
                plt.plot(T_data, Y_data, 'o-', label='Original', alpha=0.7)
                plt.plot(T_data, Y_pred, 's-', label='Fitted', alpha=0.7)
            
            plt.xlabel('Time')
            plt.ylabel('Response')
            plt.legend()
            plt.title('LocalBivariate Fitting Result')
            plt.grid(True)
            
            # 保存图片
            output_path = 'tests/localbivariate_test_result.png'
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"\n[10] 图片已保存: {output_path}")
            
        else:
            print(f"\n[ERROR] model_runner返回格式错误: {type(result)}")
            
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            print(f"\n[清理] 临时文件已删除")


if __name__ == '__main__':
    test_localbivariate_with_single_column()

