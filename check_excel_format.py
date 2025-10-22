"""
检查Excel文件格式
"""
import pandas as pd
import os

# 查找Excel文件
excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and '150KD' in f or 'ctla' in f.lower()]

if not excel_files:
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx')]

if not excel_files:
    print("No Excel files found")
    exit(1)

excel_file = excel_files[0]
print(f"Checking Excel file: {excel_file}\n")

try:
    df = pd.read_excel(excel_file)
    
    print(f"Shape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst 5 rows:")
    print(df.head(5))
    
    print(f"\n[OK] Excel file can be loaded!")
    print(f"\nNote: First column is '{df.columns[0]}'")
    
    # 检查第一列是否需要重命名为Time
    if df.columns[0] not in ['Time', 'time']:
        print(f"  -> First column should be renamed to 'Time' for fitting")
        print(f"  -> Current name: '{df.columns[0]}'")
    
    # 检查其他列是否是数值
    other_cols = df.columns[1:]
    print(f"\nOther columns: {list(other_cols)}")
    
    try:
        concentrations = [float(str(col)) for col in other_cols]
        print(f"  -> Concentrations (numeric): {concentrations}")
        print(f"  [OK] All concentration columns are numeric!")
    except (ValueError, TypeError) as e:
        print(f"  [Warning] Some columns are not numeric: {e}")
        print(f"  -> This might affect fitting")
    
except Exception as e:
    print(f"[ERROR] Failed to load Excel: {e}")
    import traceback
    traceback.print_exc()

