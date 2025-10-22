"""
测试多样本JSON加载和宽表构建
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json

# 不依赖PySide6，直接测试数据模型
from src.models.data_model import Data

def test_wide_table_loading():
    """测试从JSON加载多浓度数据"""
    print("\n" + "="*70)
    print("测试: 多浓度JSON加载 → 宽表")
    print("="*70)
    
    # 找到JSON文件
    json_files = [x for x in os.listdir('.') if x.endswith('.json')]
    if not json_files:
        print("[ERROR] 找不到JSON文件")
        return
    
    json_file = json_files[0]
    print(f"\n[1] 加载JSON: {json_file}")
    
    # 读取JSON
    with open(json_file, encoding='utf-8') as f:
        data_dict = json.load(f)
    
    print(f"   样本数: {len(data_dict['CalculateDataList'])}")
    
    # 创建Data对象（模拟加载）
    print("\n[2] 创建Data对象...")
    print("="*70)
    data = Data(item=data_dict, itemtype='file')
    print("="*70)
    
    # 检查结果
    print(f"\n[3] 加载结果:")
    print(f"   数据名称: {data.name}")
    print(f"   DataFrame形状: {data.dataframe.shape}")
    print(f"   DataFrame列名: {list(data.dataframe.columns)}")
    
    print(f"\n[4] DataFrame预览（前10行）:")
    print(data.dataframe.head(10))
    
    # 验证宽表格式
    print(f"\n[5] 验证宽表格式:")
    cols = data.dataframe.columns
    if len(cols) >= 2 and cols[0] in ['Time', 'time', 'XValue']:
        print(f"   ✅ 第一列是时间: {cols[0]}")
        
        other_cols = cols[1:]
        try:
            concentrations = [float(str(col)) for col in other_cols]
            print(f"   ✅ 其他列是浓度值: {concentrations}")
            print(f"   ✅ 宽表格式正确！")
            
            # 检查浓度是否都非零
            non_zero_concs = [c for c in concentrations if c > 0]
            print(f"\n[6] 浓度检查:")
            print(f"   总浓度数: {len(concentrations)}")
            print(f"   非零浓度数: {len(non_zero_concs)}")
            if len(non_zero_concs) < len(concentrations):
                print(f"   ⚠️ 警告：包含浓度=0的列（可能导致拟合结果为0）")
            
        except (ValueError, TypeError) as e:
            print(f"   ❌ 列名不是数值: {other_cols}")
            print(f"   错误: {e}")
    else:
        print(f"   ❌ 格式不正确: {list(cols)}")
    
    return data


if __name__ == '__main__':
    try:
        data = test_wide_table_loading()
        
        print("\n" + "="*70)
        print("✅ 测试完成！")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

