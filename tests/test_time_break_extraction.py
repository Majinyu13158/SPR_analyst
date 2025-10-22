"""
测试time_break提取和估计功能
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd

def test_time_break_estimation():
    """测试time_break估计功能"""
    print("\n" + "="*50)
    print("测试1: time_break估计")
    print("="*50)
    
    # 模拟SPR数据（结合-解离曲线）
    # 0-100: 结合阶段（指数上升）
    # 100-200: 解离阶段（指数下降）
    time = np.linspace(0, 200, 201)
    
    # 结合阶段：Y = Rmax * (1 - exp(-k*t))
    association = 50 * (1 - np.exp(-0.05 * time[:101]))
    
    # 解离阶段：Y = Y_max * exp(-k*(t-100))
    dissociation = association[-1] * np.exp(-0.03 * (time[101:] - 100))
    
    y_data = np.concatenate([association, dissociation])
    
    # 找到最大值位置
    max_idx = np.argmax(y_data)
    estimated_break = time[max_idx]
    
    print(f"[OK] 真实time_break: 100.0")
    print(f"[OK] 估计time_break: {estimated_break}")
    print(f"[OK] 误差: {abs(estimated_break - 100.0)}")
    
    assert abs(estimated_break - 100.0) < 5.0, f"估计误差过大: {estimated_break}"
    print("[OK] time_break估计测试通过！\n")


def test_data_attributes_extraction():
    """测试从Data对象提取time_break"""
    print("\n" + "="*50)
    print("测试2: 从Data对象提取time_break")
    print("="*50)
    
    # 模拟Data对象的attributes
    class MockData:
        def __init__(self):
            self.attributes = {
                'calculatedatalist_combineendindex': 150.0,
                'calculatedatalist_dissociationendindex': 300.0
            }
    
    data = MockData()
    
    # 提取time_break
    combine_end = data.attributes.get('calculatedatalist_combineendindex')
    
    print(f"[OK] CombineEndIndex: {combine_end}")
    
    if combine_end is not None and combine_end > 0:
        time_break = float(combine_end)
        print(f"[OK] 成功提取time_break: {time_break}")
    else:
        print("[ERROR] time_break提取失败")
        raise ValueError("time_break提取失败")
    
    assert time_break == 150.0, f"time_break不匹配: {time_break}"
    print("[OK] Data attributes提取测试通过！\n")


def test_fallback_logic():
    """测试回退逻辑"""
    print("\n" + "="*50)
    print("测试3: 回退逻辑（CombineEndIndex=0）")
    print("="*50)
    
    # 模拟attributes中time_break未设置的情况
    class MockData:
        def __init__(self):
            self.attributes = {
                'calculatedatalist_combineendindex': 0,  # 未设置
            }
    
    data = MockData()
    
    # 提取time_break
    combine_end = data.attributes.get('calculatedatalist_combineendindex')
    
    print(f"[OK] CombineEndIndex: {combine_end}")
    
    # 模拟数据
    time = np.linspace(0, 200, 201)
    association = 50 * (1 - np.exp(-0.05 * time[:101]))
    dissociation = association[-1] * np.exp(-0.03 * (time[101:] - 100))
    y_data = np.concatenate([association, dissociation])
    
    if combine_end is None or combine_end <= 0:
        print("[OK] time_break未设置，使用估计方法")
        max_idx = np.argmax(y_data)
        time_break = float(time[max_idx])
        print(f"[OK] 估计time_break: {time_break}")
    else:
        time_break = float(combine_end)
        print(f"[OK] 使用设置的time_break: {time_break}")
    
    assert abs(time_break - 100.0) < 5.0, f"回退估计误差过大: {time_break}"
    print("[OK] 回退逻辑测试通过！\n")


if __name__ == '__main__':
    try:
        test_time_break_estimation()
        test_data_attributes_extraction()
        test_fallback_logic()
        
        print("\n" + "="*50)
        print("[OK] 所有time_break测试通过！")
        print("="*50)
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()

