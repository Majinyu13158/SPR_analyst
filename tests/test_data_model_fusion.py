# -*- coding: utf-8 -*-
"""
测试融合版 Data 类
验证：
1. 从JSON加载（原项目25个属性）
2. 从DataFrame创建（新项目方式）
3. 智能XY提取
4. 属性统一访问
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from src.models.data_model import Data, DataManager


def test_json_loading():
    """测试1：从JSON加载（原项目风格）"""
    print("=" * 50)
    print("测试1：从JSON加载（原项目风格）")
    print("=" * 50)
    
    # 模拟原项目的JSON结构
    json_data = {
        "CalculateDataSource": 1,
        "CalculateDataType": 1,
        "CalculateFormula": 102,
        "FittingOptions": {
            "KDBound": -15,
            "PunishUpper": 40,
            "PunishLower": -16,
            "PunishK": 2
        },
        "CalculateDataList": [
            {
                "ExperimentID": 1836307608651304960,
                "SampleID": 1836307608689053696,
                "Molecular": 150000.0,
                "SampleName": "多循环igg",
                "Concentration": 0.0,
                "ConcentrationUnit": "M",
                "HoleType": None,
                "BaseStartIndex": None,
                "CombineStartIndex": 0,
                "CombineEndIndex": 100,
                "DissociationEndIndex": None,
                "BaseData": [
                    {"Time": 0.0, "XValue": 0.0, "YValue": 0.0},
                    {"Time": 1.0, "XValue": 1.0, "YValue": -0.43},
                    {"Time": 2.0, "XValue": 2.0, "YValue": 0.56},
                    {"Time": 3.0, "XValue": 3.0, "YValue": 1.2},
                    {"Time": 4.0, "XValue": 4.0, "YValue": 0.8},
                ]
            }
        ]
    }
    
    # 创建Data对象
    data = Data(item=json_data, itemtype='file')
    
    # 验证基本信息
    print(f"✓ 数据名称: {data.get_name()}")
    assert data.get_name() == "多循环igg", "名称提取失败"
    
    # 验证25个默认属性
    print(f"✓ 拟合公式: {data.attributes['fittingformula']}")
    assert data.attributes['fittingformula'] == 102
    
    print(f"✓ KDBound: {data.attributes['fittingoptions_kdbound']}")
    assert data.attributes['fittingoptions_kdbound'] == -15
    
    print(f"✓ 样本名称: {data.attributes['calculatedatalist_samplename']}")
    assert data.attributes['calculatedatalist_samplename'] == "多循环igg"
    
    print(f"✓ 浓度: {data.attributes['calculatedatalist_concentration']}")
    assert data.attributes['calculatedatalist_concentration'] == 0.0
    
    print(f"✓ 分子量: {data.attributes['calculatedatalist_molecular']}")
    assert data.attributes['calculatedatalist_molecular'] == 150000.0
    
    # 验证DataFrame转换
    df = data.get_processed_data()
    print(f"✓ DataFrame形状: {df.shape}")
    assert df.shape == (5, 3), "DataFrame形状不正确"
    
    # 验证智能XY提取
    x, y = data.get_xy_data()
    print(f"✓ X数据: {x}")
    print(f"✓ Y数据: {y}")
    assert len(x) == len(y) == 5, "XY数据长度不匹配"
    
    print("✅ 测试1通过！\n")


def test_dataframe_creation():
    """测试2：从DataFrame创建（新项目风格）"""
    print("=" * 50)
    print("测试2：从DataFrame创建（新项目风格）")
    print("=" * 50)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'Time': [0, 1, 2, 3, 4, 5],
        'Response': [0.1, 0.3, 0.5, 0.4, 0.2, 0.15]
    })
    
    # 创建Data对象
    data = Data(item=df, itemtype='dataframe')
    data.set_name("实验数据A")
    
    # 验证
    print(f"✓ 数据名称: {data.get_name()}")
    assert data.get_name() == "实验数据A"
    
    # 验证DataFrame
    df_loaded = data.get_processed_data()
    print(f"✓ DataFrame形状: {df_loaded.shape}")
    assert df_loaded.shape == (6, 2)
    
    # 验证智能XY提取
    x, y = data.get_xy_data()
    print(f"✓ X数据长度: {len(x)}")
    print(f"✓ Y数据长度: {len(y)}")
    assert len(x) == len(y) == 6
    
    print("✅ 测试2通过！\n")


def test_attribute_access():
    """测试3：统一属性访问"""
    print("=" * 50)
    print("测试3：统一属性访问（默认+扩展）")
    print("=" * 50)
    
    data = Data(item=None, itemtype='dataframe')
    
    # 设置默认属性
    data.set_attribute('fittingformula', 999)
    assert data.get_attribute('fittingformula') == 999
    print(f"✓ 默认属性设置成功: fittingformula=999")
    
    # 设置扩展属性
    data.set_attribute('custom_field', '自定义值')
    assert data.get_attribute('custom_field') == '自定义值'
    print(f"✓ 扩展属性设置成功: custom_field=自定义值")
    
    # 验证扩展属性在extra_attributes中
    assert 'custom_field' in data.extra_attributes
    print(f"✓ 扩展属性存储在 extra_attributes")
    
    # 验证默认属性在attributes中
    assert 'fittingformula' in data.attributes
    print(f"✓ 默认属性存储在 attributes")
    
    print("✅ 测试3通过！\n")


def test_data_manager():
    """测试4：DataManager统一接口"""
    print("=" * 50)
    print("测试4：DataManager统一接口")
    print("=" * 50)
    
    dm = DataManager()
    
    # 方式1：从DataFrame添加
    df1 = pd.DataFrame({'Time': [0, 1, 2], 'Response': [0.1, 0.2, 0.3]})
    id1 = dm.add_data("样本A", df1)
    print(f"✓ DataFrame方式添加成功，ID={id1}")
    
    # 方式2：从JSON添加
    json_data = {
        "CalculateDataSource": 1,
        "CalculateDataList": [{
            "SampleName": "样本B",
            "Concentration": 10.5,
            "BaseData": [
                {"Time": 0, "YValue": 0.5},
                {"Time": 1, "YValue": 1.0},
            ]
        }]
    }
    id2 = dm.add_data(json_data, 'file')
    print(f"✓ JSON方式添加成功，ID={id2}")
    
    # 验证获取
    data1 = dm.get_data(id1)
    data2 = dm.get_data(id2)
    
    assert data1.get_name() == "样本A"
    assert data2.get_name() == "样本B"
    print(f"✓ 数据获取成功: {data1.get_name()}, {data2.get_name()}")
    
    # 验证计数
    assert dm.get_data_count() == 2
    print(f"✓ 数据计数正确: {dm.get_data_count()}")
    
    # 验证删除
    dm.remove_data(id1)
    assert dm.get_data_count() == 1
    print(f"✓ 删除数据成功，剩余: {dm.get_data_count()}")
    
    print("✅ 测试4通过！\n")


def test_smart_xy_extraction():
    """测试5：智能XY提取的鲁棒性"""
    print("=" * 50)
    print("测试5：智能XY提取的鲁棒性")
    print("=" * 50)
    
    # 测试带单位的数据
    df = pd.DataFrame({
        'Time': ['0 sec', '1.0 sec', '2.5 sec'],
        'Signal': ['100 RU', '200 RU', '150 RU'],
        'Concentration': [1, 1, 1],  # 应该被排除
        'Index': [0, 1, 2]  # 应该被排除
    })
    
    data = Data(item=df, itemtype='dataframe')
    x, y = data.get_xy_data()
    
    print(f"✓ X数据（自动解析单位）: {x}")
    print(f"✓ Y数据（自动解析单位）: {y}")
    assert len(x) == 3
    assert len(y) == 3
    assert x[0] == 0.0
    assert y[0] == 100.0
    
    print("✅ 测试5通过！\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("开始测试融合版 Data 类")
    print("=" * 60 + "\n")
    
    try:
        test_json_loading()
        test_dataframe_creation()
        test_attribute_access()
        test_data_manager()
        test_smart_xy_extraction()
        
        print("=" * 60)
        print("🎉 所有测试通过！融合版Data类工作正常！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

