"""
读取旧项目使用的Excel文件
"""
import pandas as pd
import os

# 查找Excel文件
for f in os.listdir('.'):
    if f.endswith('.xlsx') and '150KD' in f:
        excel_file = f
        print(f"Found Excel: {excel_file}")
        
        try:
            df = pd.read_excel(excel_file)
            
            print(f"\nShape: {df.shape}")
            print(f"\nColumns: {list(df.columns)}")
            print(f"\nFirst 10 rows:")
            print(df.head(10))
            print(f"\nLast 5 rows:")
            print(df.tail(5))
            
            # 检查数据统计
            print(f"\nData statistics:")
            print(df.describe())
            
            # 检查列名是否是浓度
            cols = list(df.columns)
            if len(cols) >= 2:
                print(f"\nFirst column: {cols[0]}")
                print(f"Other columns: {cols[1:]}")
                
                # 尝试将其他列名转为浮点数
                try:
                    concs = [float(str(col)) for col in cols[1:]]
                    print(f"Concentrations: {concs}")
                except:
                    print("Columns are not numeric concentrations")
            
        except Exception as e:
            print(f"Error reading Excel: {e}")
            import traceback
            traceback.print_exc()
        
        break

