import json
import pandas as pd
import numpy as np
from XlementFitting.FittingOptions import FittingOptions

def read_and_process_json(json_path):
    # 读取JSON文件
    with open(json_path, 'r', encoding='utf-8-sig') as file:
        data = json.load(file)
    
    # 提取FittingOptions
    fitting_options = data['FittingOptions']
    
    # 处理CalculateDataList
    sample_data = {}
    all_x_values = set()
    max_combine_x = float('-inf')
    
    for sample in data['CalculateDataList']:
        sample_id = sample['SampleID']
        concentration = sample['Concentration']
        
        # 处理CombineData
        combine_data = sample['CombineData']
        combine_x_values = [point['XValue'] for point in combine_data]
        if combine_x_values:
            max_combine_x = max(max_combine_x, max(combine_x_values))
        
        # 合并CombineData和DissociationData，并按ID排序
        combined_data = sorted(sample['CombineData'] + sample['DissociationData'], 
                               key=lambda x: x['ID'], reverse=True)
        
        # 提取X值和Y值，并创建字典
        xy_dict = {point['XValue']: point['YValue'] for point in combined_data}
        
        # 更新所有可能的X值
        all_x_values.update(xy_dict.keys())
        
        sample_data[sample_id] = {
            'concentration': concentration,
            'xy_dict': xy_dict
        }
    
    # 对所有X值排序
    sorted_x_values = sorted(all_x_values)
    
    # 创建DataFrame
    df_data = {'XValue': sorted_x_values}
    for sample_id, sample in sample_data.items():
        y_values = [sample['xy_dict'].get(x, np.nan) for x in sorted_x_values]
        df_data[sample_id] = y_values
    
    df = pd.DataFrame(df_data)
    
    # 添加浓度行
    concentrations = {sid: data['concentration'] for sid, data in sample_data.items()}
    concentration_row = pd.DataFrame([concentrations], columns=df.columns[1:])
    concentration_row.insert(0, 'XValue', np.nan)  # XValue列为空
    df = pd.concat([concentration_row, df], ignore_index=True)
    
    return fitting_options, df, max_combine_x, data['CalculateFormula']

def get_fitting_options(
    fitting_options_dict: dict
)->FittingOptions:
    customized_fitting_options = FittingOptions()
    customized_fitting_options.set_KD_bound(fitting_options_dict['KDBound'])
    customized_fitting_options.set_punish_lower(fitting_options_dict['PunishLower'])
    customized_fitting_options.set_punish_upper(fitting_options_dict['PunishUpper'])
    customized_fitting_options.set_punish_k(fitting_options_dict['PunishK'])
    return customized_fitting_options

def transform_dataframe(df):
    # 提取 X 值（第一列，跳过第一行的浓度）
    X_values = df['XValue'].iloc[1:].to_numpy()

    # 提取 Y 值（跳过第一列和第一行）
    Y_data = df.iloc[1:, 1:].to_numpy().T

    # 提取浓度（第一行，跳过第一列）
    concentrations = df.iloc[0, 1:].to_numpy()

    # 创建 A_data（浓度重复到与 Y_data 相同的大小）
    A_data = np.tile(concentrations, (len(X_values), 1)).T

    # 创建 X_data（X 值重复到与 Y_data 相同的大小）
    X_data = np.tile(X_values, (Y_data.shape[0], 1))

    # 将 X_data 相对于最小值归零
    X_data = X_data - np.min(X_data)

    return Y_data, A_data, X_data

