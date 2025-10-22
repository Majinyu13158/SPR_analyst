import json
import os

json_files = [x for x in os.listdir('.') if x.endswith('.json')]
if not json_files:
    print("No JSON files")
    exit(1)

json_file = json_files[0]
print(f"File: {json_file}\n")

with open(json_file, encoding='utf-8') as f:
    data = json.load(f)

sample = data['CalculateDataList'][0]

print("Index information:")
print(f"  CombineStartIndex: {sample.get('CombineStartIndex')}")
print(f"  CombineEndIndex: {sample.get('CombineEndIndex')}")
print(f"  DissociationEndIndex: {sample.get('DissociationEndIndex')}")
print(f"  BaseStartIndex: {sample.get('BaseStartIndex')}")

print(f"\nData arrays:")
print(f"  BaseData length: {len(sample.get('BaseData', []))}")
print(f"  CombineData length: {len(sample.get('CombineData', []))}")
print(f"  DissociationData length: {len(sample.get('DissociationData', []))}")

# Check if we should combine all data
total_data = []
if 'BaseData' in sample:
    total_data.extend(sample['BaseData'])
if 'CombineData' in sample:
    total_data.extend(sample['CombineData'])
if 'DissociationData' in sample:
    total_data.extend(sample['DissociationData'])

print(f"\nTotal data points (Base+Combine+Dissociation): {len(total_data)}")

if total_data:
    times = [d.get('XValue', 0) for d in total_data]
    print(f"Time range: {min(times)} ~ {max(times)}")

