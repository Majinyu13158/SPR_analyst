import json
import pandas as pd

def update_json_with_dataframe(json_data, df):
    # 深拷贝JSON数据以避免修改原始数据
    updated_json = json.loads(json.dumps(json_data))
    
    for sample in updated_json['CalculateDataList']:
        sample_id = int(sample['SampleID'])
        if sample_id in list(df.columns):
            for data_type in ['BaseData', 'CombineData', 'DissociationData']:
                if sample[data_type] is not None:
                    for item in sample[data_type]:
                        x_value = item['XValue']
                        # 在DataFrame中查找对应的Y值
                        y_prediction = df.loc[df['XValue'] == x_value, sample_id].values
                        
                        if len(y_prediction) > 0:
                            item['YPrediction'] = float(y_prediction[0])
                        else:
                            item['YPrediction'] = 0.0  # 或者可以选择不添加这个键
    
    return updated_json

# 使用函数
def process_and_save_json(json_file_path, df, output_json_path, fitting_result):
    # 读取原始JSON文件
    with open(json_file_path, 'r', encoding='utf-8-sig') as file:
        original_json = json.load(file)
    
    # 更新JSON
    updated_json = update_json_with_dataframe(original_json, df)
    
    # 添加FittingResult
    updated_json['FittingResult'] = fitting_result
    
    # 保存更新后的JSON
    with open(output_json_path, 'w', encoding='utf-8-sig') as file:
        json.dump(updated_json, file, indent=4)

# 使用示例
# json_file_path = 'path_to_your_input_json_file.json'
# df = your_dataframe  # 您的pandas DataFrame
# output_json_path = 'path_to_your_output_json_file.json'
# process_and_save_json(json_file_path, df, output_json_path)
