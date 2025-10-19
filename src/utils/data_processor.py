# -*- coding: utf-8 -*-
"""
数据处理工具 - 完全参考原项目实现

功能：
- 加载JSON/Excel文件（支持原项目的所有JSON格式）
- 数据预处理和标准化
- 数据格式转换

参考：
- XlementFitting/FileProcess/Json2Data.py - 用于CalculateDataList格式
- XlementFitting/FileProcess/XlementDataFrame.py - 用于OriginalDataList格式
- spr_gui_main.py - GUI显示逻辑
"""
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional


class DataProcessor:
    """
    数据处理器 - 完全参考原项目逻辑
    
    提供各种数据处理功能
    """
    
    @staticmethod
    def load_json(file_path: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        加载JSON文件
        
        返回:
            (success, data_dict, error_message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return True, data, None
        except FileNotFoundError:
            return False, None, f"文件不存在: {file_path}"
        except json.JSONDecodeError as e:
            return False, None, f"JSON格式错误: {str(e)}"
        except Exception as e:
            return False, None, f"读取文件失败: {str(e)}"
    
    @staticmethod
    def load_excel(file_path: str, sheet_name: str = None) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
        """
        加载Excel文件
        
        参数:
            file_path: 文件路径
            sheet_name: 工作表名（None=第一个）
        
        返回:
            (success, dataframe, error_message)
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            return True, df, None
        except FileNotFoundError:
            return False, None, f"文件不存在: {file_path}"
        except Exception as e:
            return False, None, f"读取Excel失败: {str(e)}"
    
    @staticmethod
    def json_to_dataframe(json_data: Dict) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
        """
        JSON数据转DataFrame（完全参考原项目逻辑）
        
        支持格式：
        1. 新格式（Json2Data.py）：包含BaseData、CombineData、DissociationData
        2. 旧格式（XlementDataFrame.py）：包含OriginalDataList
        
        返回:
            (success, dataframe, error_message)
        """
        try:
            print(f"\n{'='*80}")
            print(f"[DataProcessor] 开始解析JSON数据")
            print(f"{'='*80}")
            
            # 检查是否有CalculateDataList
            if not isinstance(json_data, dict):
                return False, None, "JSON根节点必须是字典"
            
            if 'CalculateDataList' not in json_data:
                return False, None, "JSON中缺少CalculateDataList字段"
            
            calculate_list = json_data['CalculateDataList']
            
            if not isinstance(calculate_list, list) or len(calculate_list) == 0:
                return False, None, "CalculateDataList为空或格式错误"
            
            print(f"[DataProcessor] 发现 {len(calculate_list)} 个样本")
            
            # 检测JSON格式
            first_sample = calculate_list[0]
            has_original_data = 'OriginalDataList' in first_sample
            has_base_data = 'BaseData' in first_sample
            has_combine_data = 'CombineData' in first_sample
            has_dissociation_data = 'DissociationData' in first_sample
            
            print(f"[DataProcessor] JSON格式检测:")
            print(f"  - OriginalDataList: {'✓' if has_original_data else '✗'}")
            print(f"  - BaseData: {'✓' if has_base_data else '✗'}")
            print(f"  - CombineData: {'✓' if has_combine_data else '✗'}")
            print(f"  - DissociationData: {'✓' if has_dissociation_data else '✗'}")
            
            # 选择合适的解析方法
            if has_original_data:
                print(f"[DataProcessor] → 使用旧格式解析（XlementDataFrame方式）")
                df = DataProcessor._parse_original_format(calculate_list)
            else:
                print(f"[DataProcessor] → 使用新格式解析（Json2Data + GUI显示方式）")
                df = DataProcessor._parse_calculate_format(calculate_list)
            
            if df is None or df.empty:
                return False, None, "解析后的DataFrame为空"
            
            # 保存顶层元信息到attrs
            if 'FittingOptions' in json_data:
                df.attrs['fitting_options'] = json_data['FittingOptions']
                print(f"[DataProcessor] 保存FittingOptions: {json_data['FittingOptions']}")
            
            if 'CalculateFormula' in json_data:
                df.attrs['calculate_formula'] = json_data['CalculateFormula']
                print(f"[DataProcessor] 保存CalculateFormula: {json_data['CalculateFormula']}")
            
            if 'CalculateDataSource' in json_data:
                df.attrs['calculate_data_source'] = json_data['CalculateDataSource']
            
            if 'CalculateDataType' in json_data:
                df.attrs['calculate_data_type'] = json_data['CalculateDataType']
            
            # 打印详细统计信息
            print(f"\n[DataProcessor] ✅ 成功解析JSON文件")
            print(f"  - 总行数: {len(df)}")
            print(f"  - 列名: {list(df.columns)}")
            if 'XValue' in df.columns:
                print(f"  - XValue范围: [{df['XValue'].min():.2f}, {df['XValue'].max():.2f}]")
            if 'YValue' in df.columns:
                print(f"  - YValue范围: [{df['YValue'].min():.2f}, {df['YValue'].max():.2f}]")
            
            # 显示前后几行
            print(f"\n前3行数据:")
            print(df.head(3).to_string())
            print(f"\n后3行数据:")
            print(df.tail(3).to_string())
            print(f"{'='*80}\n")
            
            return True, df, None
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, None, f"转换DataFrame失败: {str(e)}"
    
    @staticmethod
    def _parse_calculate_format(calculate_list: List[dict]) -> pd.DataFrame:
        """
        解析新格式JSON（BaseData + CombineData + DissociationData）
        
        参考：
        - XlementFitting/FileProcess/Json2Data.py：read_and_process_json() 合并CombineData和DissociationData用于拟合
        - spr_gui_main.py：fillTable() 显示BaseData和CombineData到表格
        
        本实现参考GUI显示逻辑：显示BaseData和CombineData（如果有）
        
        参数:
            calculate_list: CalculateDataList数组
            
        返回:
            DataFrame
        """
        all_data = []
        total_base = 0
        total_combine = 0
        total_dissociation = 0
        
        for i, sample in enumerate(calculate_list):
            sample_id = sample.get('SampleID', f'sample_{i}')
            sample_name = sample.get('SampleName', f'Sample {i+1}')
            concentration = sample.get('Concentration', 0.0)
            
            print(f"[DataProcessor] 样本 {i+1}/{len(calculate_list)}: {sample_name}")
            
            # 提取BaseData（参考spr_gui_main.py第825行）
            if 'BaseData' in sample:
                base_data = sample['BaseData']
                if isinstance(base_data, list) and base_data:
                    all_data.extend(base_data)
                    total_base += len(base_data)
                    print(f"  - BaseData: {len(base_data)} 个数据点")
            
            # 提取CombineData（参考spr_gui_main.py第826-828行）
            if 'CombineData' in sample:
                combine_data = sample['CombineData']
                if isinstance(combine_data, list) and combine_data:
                    all_data.extend(combine_data)
                    total_combine += len(combine_data)
                    print(f"  - CombineData: {len(combine_data)} 个数据点")
            
            # 提取DissociationData（可选，某些场景需要）
            if 'DissociationData' in sample:
                dissociation_data = sample['DissociationData']
                if isinstance(dissociation_data, list) and dissociation_data:
                    all_data.extend(dissociation_data)
                    total_dissociation += len(dissociation_data)
                    print(f"  - DissociationData: {len(dissociation_data)} 个数据点")
        
        print(f"[DataProcessor] 数据统计:")
        print(f"  - BaseData总计: {total_base}")
        print(f"  - CombineData总计: {total_combine}")
        print(f"  - DissociationData总计: {total_dissociation}")
        print(f"  - 总数据点: {len(all_data)}")
        
        if not all_data:
            print("[DataProcessor] ❌ 警告: 没有找到任何数据")
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(all_data)
        
        # 保存第一个样本的元信息
        if calculate_list:
            first_sample = calculate_list[0]
            df.attrs['sample_name'] = first_sample.get('SampleName', 'Unknown')
            df.attrs['sample_id'] = first_sample.get('SampleID', 0)
            df.attrs['concentration'] = first_sample.get('Concentration', 0.0)
            df.attrs['molecular'] = first_sample.get('Molecular', 0.0)
            df.attrs['concentration_unit'] = first_sample.get('ConcentrationUnit', 'M')
        
        return df
    
    @staticmethod
    def _parse_original_format(calculate_list: List[dict]) -> pd.DataFrame:
        """
        解析旧格式JSON（OriginalDataList）
        
        参考: XlementFitting/FileProcess/XlementDataFrame.py的_format_json方法
        
        这种格式的JSON结构：
        - OriginalDataList: 原始数据列表，包含ID和Value
        - BaseStartIndex, CombineStartIndex, CombineEndIndex, DissociationEndIndex: 时间分割点
        
        参数:
            calculate_list: CalculateDataList数组
            
        返回:
            DataFrame
        """
        all_data = []
        
        for i, sample in enumerate(calculate_list):
            sample_id = sample.get('SampleID', f'sample_{i}')
            sample_name = sample.get('SampleName', f'Sample {i+1}')
            concentration = sample.get('Concentration', 0.0)
            
            print(f"[DataProcessor] 样本 {i+1}/{len(calculate_list)}: {sample_name}")
            
            # 提取OriginalDataList
            original_data = sample.get('OriginalDataList', [])
            if not original_data:
                print(f"  - ❌ 没有OriginalDataList")
                continue
            
            # 按ID排序（参考原项目XlementDataFrame.py第91行）
            sorted_data = sorted(original_data, key=lambda x: x.get('ID', 0))
            print(f"  - OriginalDataList: {len(sorted_data)} 个数据点")
            
            # 转换为标准格式
            for idx, item in enumerate(sorted_data):
                data_point = {
                    'ID': item.get('ID', idx),
                    'XValue': float(idx),  # 使用索引作为XValue
                    'YValue': item.get('Value', 0.0),
                    'Time': item.get('Time'),
                    'YPrediction': 0.0
                }
                all_data.append(data_point)
            
            # 打印时间分割点
            if 'BaseStartIndex' in sample:
                print(f"  - BaseStartIndex: {sample['BaseStartIndex']}")
                print(f"  - CombineStartIndex: {sample['CombineStartIndex']}")
                print(f"  - CombineEndIndex: {sample['CombineEndIndex']}")
                print(f"  - DissociationEndIndex: {sample['DissociationEndIndex']}")
        
        if not all_data:
            print("[DataProcessor] ❌ 警告: 没有找到任何数据")
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(all_data)
        
        # 保存第一个样本的元信息
        if calculate_list:
            first_sample = calculate_list[0]
            df.attrs['sample_name'] = first_sample.get('SampleName', 'Unknown')
            df.attrs['sample_id'] = first_sample.get('SampleID', 0)
            df.attrs['concentration'] = first_sample.get('Concentration', 0.0)
            df.attrs['molecular'] = first_sample.get('Molecular', 0.0)
            df.attrs['concentration_unit'] = first_sample.get('ConcentrationUnit', 'M')
        
        print(f"[DataProcessor] 总数据点: {len(all_data)}")
        
        return df
    
    @staticmethod
    def validate_spr_data(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
        """
        验证SPR数据格式
        
        必须包含：
        - XValue或Time列
        - YValue或Response列
        
        返回:
            (is_valid, error_message)
        """
        if df is None or df.empty:
            return False, "数据为空"
        
        # 检查X列
        x_columns = ['XValue', 'Time', 'x', 'time']
        has_x = any(col in df.columns for col in x_columns)
        
        if not has_x:
            return False, f"缺少X轴数据列（需要: {', '.join(x_columns)}）"
        
        # 检查Y列
        y_columns = ['YValue', 'Response', 'y', 'response']
        has_y = any(col in df.columns for col in y_columns)
        
        if not has_y:
            return False, f"缺少Y轴数据列（需要: {', '.join(y_columns)}）"
        
        return True, None
    
    @staticmethod
    def normalize_spr_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化SPR数据格式
        
        统一列名为：XValue, YValue
        添加ID列
        """
        df_copy = df.copy()
        
        # 标准化X列
        if 'Time' in df_copy.columns:
            df_copy['XValue'] = df_copy['Time']
        elif 'time' in df_copy.columns:
            df_copy['XValue'] = df_copy['time']
        elif 'x' in df_copy.columns:
            df_copy['XValue'] = df_copy['x']
        
        # 标准化Y列
        if 'Response' in df_copy.columns:
            df_copy['YValue'] = df_copy['Response']
        elif 'response' in df_copy.columns:
            df_copy['YValue'] = df_copy['response']
        elif 'y' in df_copy.columns:
            df_copy['YValue'] = df_copy['y']
        
        # 添加ID列（如果没有）
        if 'ID' not in df_copy.columns:
            df_copy['ID'] = range(1, len(df_copy) + 1)
        
        # 只保留需要的列
        keep_columns = ['ID', 'XValue', 'YValue']
        if 'YPrediction' in df_copy.columns:
            keep_columns.append('YPrediction')
        
        available_columns = [col for col in keep_columns if col in df_copy.columns]
        df_normalized = df_copy[available_columns]
        
        return df_normalized
    
    @staticmethod
    def clean_data(df: pd.DataFrame, remove_nan: bool = True, remove_duplicates: bool = False) -> pd.DataFrame:
        """
        清洗数据
        
        参数:
            df: 数据框
            remove_nan: 删除NaN值
            remove_duplicates: 删除重复行
        
        返回:
            清洗后的数据框
        """
        df_clean = df.copy()
        
        if remove_nan:
            df_clean = df_clean.dropna()
        
        if remove_duplicates:
            df_clean = df_clean.drop_duplicates()
        
        return df_clean
    
    @staticmethod
    def extract_xy_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        从DataFrame提取X和Y数据
        
        返回:
            (x_array, y_array)
        """
        # 查找X列
        x_col = None
        for col_name in ['XValue', 'Time', 'x', 'time']:
            if col_name in df.columns:
                x_col = col_name
                break
        
        # 查找Y列
        y_col = None
        for col_name in ['YValue', 'Response', 'y', 'response']:
            if col_name in df.columns:
                y_col = col_name
                break
        
        if x_col is None or y_col is None:
            raise ValueError("无法找到X或Y列")
        
        x_data = df[x_col].to_numpy()
        y_data = df[y_col].to_numpy()
        
        return x_data, y_data
    
    @staticmethod
    def get_data_summary(df: pd.DataFrame) -> str:
        """
        获取数据摘要
        
        返回:
            摘要字符串
        """
        if df is None or df.empty:
            return "数据为空"
        
        summary_lines = [
            f"数据行数: {len(df)}",
            f"数据列数: {len(df.columns)}",
            f"列名: {', '.join(df.columns.tolist())}",
            "",
            "数据统计:",
            df.describe().to_string()
        ]
        
        return "\n".join(summary_lines)


# 快捷函数

def load_file(file_path: str) -> Tuple[bool, Optional[pd.DataFrame], Optional[str]]:
    """
    智能加载文件（自动识别格式）
    
    返回:
        (success, dataframe, error_message)
    """
    file_path_obj = Path(file_path)
    suffix = file_path_obj.suffix.lower()
    
    processor = DataProcessor()
    
    if suffix == '.json':
        print(f"[load_file] 开始加载JSON文件: {file_path}")
        
        # 1. 读取JSON
        success, json_data, error = processor.load_json(str(file_path))
        if not success:
            print(f"[load_file] JSON读取失败: {error}")
            return False, None, error
        
        print(f"[load_file] JSON读取成功")
        
        # 2. 转换为DataFrame
        success, df, error = processor.json_to_dataframe(json_data)
        if not success:
            print(f"[load_file] DataFrame转换失败: {error}")
            return False, None, error
        
        print(f"[load_file] DataFrame转换成功: shape={df.shape}")
        
        return True, df, None
    
    elif suffix in ['.xlsx', '.xls']:
        print(f"[load_file] 开始加载Excel文件: {file_path}")
        
        success, df, error = processor.load_excel(str(file_path))
        if not success:
            print(f"[load_file] Excel读取失败: {error}")
            return False, None, error
        
        return True, df, None
    
    else:
        return False, None, f"不支持的文件格式: {suffix}"
