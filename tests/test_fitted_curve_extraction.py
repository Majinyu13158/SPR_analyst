# -*- coding: utf-8 -*-
"""
测试拟合曲线的XY提取
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np


def test_fitted_curve_xy_extraction():
    """测试拟合曲线DataFrame的XY提取"""
    print("=" * 60)
    print("测试拟合曲线的XY提取")
    print("=" * 60)
    
    # 模拟拟合曲线的DataFrame（与controller中创建的一致）
    x_data = np.array([0, 1, 2, 3, 4])
    y_pred = np.array([0.1, 0.3, 0.5, 0.7, 0.9])  # 预测值
    
    fitted_df = pd.DataFrame({
        'XValue': x_data,
        'YValue': y_pred
    })
    
    print(f"DataFrame内容：")
    print(fitted_df)
    print(f"\n列名: {list(fitted_df.columns)}")
    
    # 模拟智能XY选择
    preferred_x = ['Time', 'time', 'XValue', 'X', 'x', 't', 'sec', 'seconds']
    preferred_y = ['Response', 'response', 'RU', 'YValue', 'y', 'signal', 'Signal', 'Value']
    
    # 选择X列
    x_col = None
    for col in preferred_x:
        if col in fitted_df.columns:
            x_col = col
            break
    
    # 选择Y列
    y_col = None
    blacklist = set(['Concentration', 'Index', 'ID'])
    candidates = [c for c in fitted_df.columns if c != x_col and c not in blacklist]
    
    for col in preferred_y:
        if col in candidates:
            y_col = col
            break
    
    print(f"\n智能选择结果：")
    print(f"  X列: {x_col}")
    print(f"  Y列: {y_col}")
    
    # 提取数据
    x_extracted = fitted_df[x_col].to_numpy()
    y_extracted = fitted_df[y_col].to_numpy()
    
    print(f"\n提取的数据：")
    print(f"  X: {x_extracted}")
    print(f"  Y: {y_extracted}")
    
    # 验证
    assert x_col == 'XValue', f"X列应该是'XValue'，实际是'{x_col}'"
    assert y_col == 'YValue', f"Y列应该是'YValue'，实际是'{y_col}'"
    assert np.array_equal(x_extracted, x_data), "X数据应该匹配"
    assert np.array_equal(y_extracted, y_pred), "Y数据应该匹配预测值"
    
    # 检查是否会画成直线（y=x）
    if np.array_equal(y_extracted, x_extracted):
        print("\n[ERROR] Y数据等于X数据，会画成直线！")
        return False
    else:
        print("\n[OK] Y数据正确，不是X数据")
        return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("验证拟合曲线XY提取")
    print("=" * 70 + "\n")
    
    try:
        result = test_fitted_curve_xy_extraction()
        
        if result:
            print("\n" + "=" * 70)
            print("[SUCCESS] 拟合曲线XY提取逻辑正确")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("[FAIL] 拟合曲线XY提取有问题")
            print("=" * 70)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

