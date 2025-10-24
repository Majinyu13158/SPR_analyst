from XlementFitting import PartialBivariate, LocalBivariate, GlobalBivariate
from XlementFitting import FittingOptions
from XlementFitting import XlementDataFrame
import json
from pathlib import Path
import numpy as np

# 所有多循环拟合的入口
# 从一个options.json作为入口

OUTPUT_TYPE = ['Biv2Excel', 'OldFasionTXT']

# 转换longdouble为float
def convert_to_float(obj):
    if isinstance(obj, dict):
        return {key: convert_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_float(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.astype(float).tolist()
    else:
        try:
            return float(obj)
        except (TypeError, ValueError):
            return obj  # 如果无法转换为 float，则保持原值

def XlementFittingFunction(
    option_json_path: str,
    output_type:str = 'OldFasionTXT'
):
    if output_type not in OUTPUT_TYPE:
        raise ValueError("选择正确的返回格式")
    
    with open(option_json_path, 'r', encoding='utf-8-sig') as file:
        opt = file.read()
    opts = json.loads(opt)

    one_excel = XlementDataFrame(opts['init_options']) # type: ignore
    # 处理数据
    one_excel_df = one_excel.process(opts['data_processing_pipeline'])
    # 读取路径
    target_path = Path(opts['init_options']['file_path'])
    # 生成一个同名的Excel文件路径
    target_path = target_path.with_name(target_path.stem + '_xlef').with_suffix(".xlsx") 
    # 生成Excel文件
    one_excel_df.to_excel(target_path,header=False,index=False)
    
    # 生成FittingOptions
    custom_option = FittingOptions()
    custom_option.set_KD_bound(opts['fitting_options']['KDBound'])
    custom_option.set_punish_upper(opts['fitting_options']['PunishUpper'])
    custom_option.set_punish_lower(opts['fitting_options']['PunishLower'])
    custom_option.set_punish_k(opts['fitting_options']['PunishK'])
    if opts['fitting_options']['FittingFormula'] == 'Partial':
        r,p,i = PartialBivariate(
            file_path=target_path,
            time0=one_excel.dissociation_time_start,
            options=custom_option,
            write_file=False,
            save_png=False,
            excel_path="FittingResultFile",
            png_path="FittingPlots"
        )
    elif opts['fitting_options']['KDBound'] == 'Local':
        r,p,i = LocalBivariate(
            file_path=target_path,
            time0=one_excel.dissociation_time_start,
            options=custom_option,
            write_file=False,
            save_png=False,
            excel_path="FittingResultFile",
            png_path="FittingPlots"
        )
    elif opts['fitting_options']['KDBound'] == 'Global':
        r,p,i = LocalBivariate(
            file_path=target_path,
            time0=one_excel.dissociation_time_start,
            options=custom_option,
            write_file=False,
            save_png=False,
            excel_path="FittingResultFile",
            png_path="FittingPlots"
        )
        
    return_value = {}
    return_value['Result'] = convert_to_float(r)
    return_value['prediction'] = convert_to_float(p)
    
    # 还需要读取原始时间, 展示时间
    return return_value