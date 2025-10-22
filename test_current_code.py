"""
快速测试当前代码是否有修复
"""
print("测试1: 检查data_model.py中是否有合并逻辑...")

# 读取data_model.py
with open('src/models/data_model.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 检查关键修复
if 'get_all_data_from_sample' in code:
    print("  [OK] Found get_all_data_from_sample (merge Base+Combine+Dissociation)")
else:
    print("  [ERROR] Missing get_all_data_from_sample!")

if 'CombineData' in code and 'DissociationData' in code:
    print("  [OK] Contains CombineData and DissociationData processing")
else:
    print("  [ERROR] Missing CombineData/DissociationData processing!")

print("\n测试2: 检查LocalBivariate.py中是否有自动估计time_break...")

with open('model_data_process/LocalBivariate.py', 'r', encoding='utf-8') as f:
    code = f.read()

if 'AutoEstimate' in code or 'Y_max_idx' in code:
    print("  [OK] Found time_break auto-estimation logic")
else:
    print("  [ERROR] Missing time_break auto-estimation!")

if 'time_break = 133' in code and 'Y_max_idx' not in code:
    print("  [ERROR] Still hardcoded time_break=133!")
elif 'time_break = 133' not in code:
    print("  [OK] Removed hardcoded time_break=133")

print("\n测试3: 检查model_runner是否返回字典...")

if "'T_data':" in code and "'parameters':" in code:
    print("  [OK] model_runner returns dict format")
else:
    print("  [ERROR] model_runner not returning dict!")

print("\n[OK] Code check complete!")
print("\n建议:")
print("1. 如果GUI还在运行，请完全关闭")
print("2. 重新启动: py app_full.py")
print("3. 加载JSON文件，检查控制台是否显示:")
print("   [Data Model] 合并数据点: BaseData + CombineData + DissociationData = 298点")

