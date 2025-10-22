"""
检查JSON中的多样本数据
"""
import json
import os

# 找到JSON文件
json_files = [x for x in os.listdir('.') if x.endswith('.json')]
if not json_files:
    print("[ERROR] No JSON file found")
    exit(1)

json_file = json_files[0]
print(f"JSON file: {json_file}")

# 加载数据
with open(json_file, encoding='utf-8') as f:
    data = json.load(f)

samples = data['CalculateDataList']
print(f"\nTotal samples: {len(samples)}")
print("\nSample information:")
print("="*80)

for i, s in enumerate(samples):
    name = s.get('SampleName', 'N/A')
    conc = s.get('Concentration', 'N/A')
    unit = s.get('ConcentrationUnit', '')
    base_data_count = len(s.get('BaseData', []))
    
    print(f"[{i}] {name:20s} | Concentration: {conc:>12} {unit:3s} | BaseData points: {base_data_count}")

# 检查是否所有样本的Time点数相同
print("\n" + "="*80)
print("Check Time alignment:")

time_lengths = []
for i, s in enumerate(samples):
    base_data = s.get('BaseData', [])
    if base_data:
        time_values = [d.get('XValue') for d in base_data]
        time_lengths.append(len(time_values))
        if i == 0:
            print(f"  Sample 0 first 5 time points: {time_values[:5]}")
        
print(f"\nAll samples have same time points? {len(set(time_lengths)) == 1}")
print(f"Time lengths: {time_lengths}")

# 显示第一个和最后一个样本的前5个数据点
print("\n" + "="*80)
print("Sample 0 (first 5 points):")
for j, d in enumerate(samples[0].get('BaseData', [])[:5]):
    print(f"  {j}: Time={d.get('XValue')}, YValue={d.get('YValue')}")

if len(samples) > 1:
    print(f"\nSample {len(samples)-1} (first 5 points):")
    for j, d in enumerate(samples[-1].get('BaseData', [])[:5]):
        print(f"  {j}: Time={d.get('XValue')}, YValue={d.get('YValue')}")

