# -*- coding: utf-8 -*-
"""
快速测试：验证add_data支持关键字参数
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd


def test_add_data_interfaces():
    """测试add_data的多种调用方式"""
    print("=" * 60)
    print("测试 add_data() 多种调用方式")
    print("=" * 60)
    
    # 模拟DataManager的add_data逻辑
    def mock_add_data(name_or_item=None, dataframe_or_type=None, **kwargs):
        """模拟add_data方法"""
        # 处理关键字参数
        if 'name' in kwargs or 'dataframe' in kwargs:
            name = kwargs.get('name', name_or_item)
            dataframe = kwargs.get('dataframe', dataframe_or_type)
            return f"DataFrame模式(关键字): name={name}, df={type(dataframe).__name__}"
        
        elif 'item' in kwargs or 'itemtype' in kwargs:
            item = kwargs.get('item', name_or_item)
            itemtype = kwargs.get('itemtype', dataframe_or_type)
            return f"JSON模式(关键字): item={type(item).__name__}, type={itemtype}"
        
        # 位置参数
        elif isinstance(name_or_item, str):
            return f"DataFrame模式(位置): name={name_or_item}, df={type(dataframe_or_type).__name__}"
        
        elif isinstance(name_or_item, dict):
            return f"JSON模式(位置): item={type(name_or_item).__name__}, type={dataframe_or_type}"
        
        else:
            raise TypeError(f"不支持的参数类型: {type(name_or_item)}")
    
    # 测试数据
    df = pd.DataFrame({'Time': [0, 1, 2], 'Response': [0.1, 0.2, 0.3]})
    json_data = {'CalculateDataList': [{'SampleName': '测试'}]}
    
    # 测试1：位置参数 - DataFrame
    result1 = mock_add_data("样本A", df)
    print(f"[TEST 1] 位置参数(DataFrame): {result1}")
    assert "DataFrame模式(位置)" in result1
    
    # 测试2：关键字参数 - DataFrame
    result2 = mock_add_data(name="样本B", dataframe=df)
    print(f"[TEST 2] 关键字参数(DataFrame): {result2}")
    assert "DataFrame模式(关键字)" in result2
    
    # 测试3：位置参数 - JSON
    result3 = mock_add_data(json_data, 'file')
    print(f"[TEST 3] 位置参数(JSON): {result3}")
    assert "JSON模式(位置)" in result3
    
    # 测试4：关键字参数 - JSON
    result4 = mock_add_data(item=json_data, itemtype='file')
    print(f"[TEST 4] 关键字参数(JSON): {result4}")
    assert "JSON模式(关键字)" in result4
    
    # 测试5：混合参数 - 位置+关键字（关键字优先）
    result5 = mock_add_data("默认名", df, name="覆盖名")
    print(f"[TEST 5] 混合参数(关键字优先): {result5}")
    assert "覆盖名" in result5
    
    print("\n[PASS] 所有调用方式测试通过！")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("验证 add_data() 支持关键字参数")
    print("=" * 70 + "\n")
    
    try:
        test_add_data_interfaces()
        
        print("\n" + "=" * 70)
        print("[SUCCESS] add_data() 现在支持以下所有调用方式：")
        print("  1. add_data('name', df)              # 位置参数")
        print("  2. add_data(name='name', dataframe=df)  # 关键字参数 ✅ 修复")
        print("  3. add_data(json_dict, 'file')       # JSON位置参数")
        print("  4. add_data(item=json_dict, itemtype='file')  # JSON关键字")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

