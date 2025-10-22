"""
测试在GUI中加载Excel数据
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication
from src.models.data_model import Data, DataManager
import pandas as pd

# 查找Excel文件
excel_file = None
for f in os.listdir('.'):
    if f.endswith('.xlsx') and '150KD' in f:
        excel_file = f
        break

if not excel_file:
    print("找不到Excel文件")
    exit(1)

print(f"Excel文件: {excel_file}")

# 创建Qt应用（data_model需要）
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# 读取Excel
df_orig = pd.read_excel(excel_file)
print(f"\n原始DataFrame: 形状={df_orig.shape}")
print(f"列名: {list(df_orig.columns)}")

# 重命名第一列为Time
df = df_orig.copy()
cols = list(df.columns)
cols[0] = 'Time'
df.columns = cols

print(f"\n处理后列名: {list(df.columns)}")
print(f"前5行:")
print(df.head(5))

# 创建DataManager
data_manager = DataManager()

# 加载为Data对象
data_id = data_manager.add_data(
    name=f"Excel: {excel_file}",
    dataframe=df
)

print(f"\n✅ 数据已加载到DataManager: data_id={data_id}")

# 验证数据
data = data_manager.get_data(data_id)
print(f"数据名称: {data.name}")
print(f"DataFrame形状: {data.dataframe.shape}")
print(f"DataFrame列名: {list(data.dataframe.columns)}")

# 测试get_xy_data
x, y = data.get_xy_data(auto_sort=False)
print(f"\nget_xy_data结果:")
print(f"  X形状: {x.shape}")
print(f"  Y形状: {y.shape}")
print(f"  X前5个值: {x[:5]}")
print(f"  Y前5个值: {y[:5]}")

print(f"\n✅ 数据加载测试成功！")
print(f"\n下一步：")
print(f"  1. 运行GUI: py app_full.py")
print(f"  2. 在GUI中点击 文件 -> 打开数据")
print(f"  3. 选择: {excel_file}")
print(f"  4. 在数据树中选择数据节点")
print(f"  5. 点击 分析 -> 拟合 -> LocalBivariate")
print(f"  6. 查看拟合结果和参数")

