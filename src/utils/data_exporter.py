# -*- coding: utf-8 -*-
"""
数据导出工具

功能：
- 导出数据为 Excel/CSV/JSON 格式
- 保留元数据信息（可选）
- 支持宽表和标准数据
"""
import json
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime
import re


class DataExporter:
    """数据导出工具类"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名中的非法字符
        
        参数:
            filename: 原始文件名
        
        返回:
            清理后的文件名
        """
        # 替换非法字符为下划线
        illegal_chars = r'[/\\:*?"<>|]'
        cleaned = re.sub(illegal_chars, '_', filename)
        # 移除前后空格
        cleaned = cleaned.strip()
        # 如果为空，使用默认名称
        if not cleaned:
            cleaned = 'data'
        return cleaned
    
    @staticmethod
    def export_to_excel(data, file_path: str, include_metadata: bool = True) -> Tuple[bool, Optional[str]]:
        """
        导出为Excel格式
        
        参数:
            data: Data对象
            file_path: 保存路径
            include_metadata: 是否包含元数据工作表
        
        返回:
            (成功, 错误信息)
        """
        try:
            # 确保路径存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            df = data.dataframe
            
            # 检查数据是否为空
            if df is None or df.empty:
                return False, "数据为空，无法导出"
            
            # 创建Excel写入器
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 写入主数据
                df.to_excel(writer, sheet_name='Data', index=False)
                
                # 可选：写入元数据
                if include_metadata:
                    metadata_rows = []
                    
                    # 基本信息
                    metadata_rows.append(['name', data.name])
                    metadata_rows.append(['itemtype', data.itemtype])
                    
                    # 25个默认属性
                    for key, value in data.attributes.items():
                        if value is not None:
                            metadata_rows.append([key, str(value)])
                    
                    # 扩展属性
                    for key, value in data.extra_attributes.items():
                        if value is not None:
                            metadata_rows.append([f'extra_{key}', str(value)])
                    
                    # 导出信息
                    metadata_rows.append(['export_time', datetime.now().isoformat()])
                    metadata_rows.append(['export_format', 'Excel'])
                    metadata_rows.append(['data_shape', f'{df.shape[0]} rows × {df.shape[1]} columns'])
                    
                    # 创建元数据DataFrame
                    metadata_df = pd.DataFrame(metadata_rows, columns=['Attribute', 'Value'])
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            print(f"✅ 数据已导出到Excel: {file_path}")
            return True, None
            
        except PermissionError:
            return False, f"文件被占用或无权限写入:\n{file_path}\n\n请关闭该文件后重试"
        except Exception as e:
            return False, f"导出Excel时发生错误:\n{str(e)}"
    
    @staticmethod
    def export_to_csv(data, file_path: str, encoding: str = 'utf-8-sig') -> Tuple[bool, Optional[str]]:
        """
        导出为CSV格式
        
        参数:
            data: Data对象
            file_path: 保存路径
            encoding: 编码格式（utf-8-sig 可被Excel正确识别）
        
        返回:
            (成功, 错误信息)
        """
        try:
            # 确保路径存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            df = data.dataframe
            
            # 检查数据是否为空
            if df is None or df.empty:
                return False, "数据为空，无法导出"
            
            # 导出CSV（使用utf-8-sig编码，Excel可以正确打开）
            df.to_csv(file_path, index=False, encoding=encoding)
            
            print(f"✅ 数据已导出到CSV: {file_path}")
            return True, None
            
        except PermissionError:
            return False, f"文件被占用或无权限写入:\n{file_path}\n\n请关闭该文件后重试"
        except Exception as e:
            return False, f"导出CSV时发生错误:\n{str(e)}"
    
    @staticmethod
    def export_to_json(data, file_path: str, indent: int = 2) -> Tuple[bool, Optional[str]]:
        """
        导出为JSON格式（包含完整信息）
        
        参数:
            data: Data对象
            file_path: 保存路径
            indent: 缩进空格数（美化格式）
        
        返回:
            (成功, 错误信息)
        """
        try:
            # 确保路径存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 构建导出数据
            export_data = {
                'name': data.name,
                'itemtype': data.itemtype,
                'dataframe': None,
                'attributes': {},
                'extra_attributes': {},
                'export_info': {
                    'export_time': datetime.now().isoformat(),
                    'export_format': 'JSON',
                    'export_version': '1.0'
                }
            }
            
            # 导出DataFrame（转为records格式）
            if data.dataframe is not None and not data.dataframe.empty:
                # 转换为字典列表，处理NaN和特殊值
                df_dict = data.dataframe.to_dict(orient='records')
                # 清理NaN值（转为null）
                import math
                def clean_value(v):
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        return None
                    return v
                
                export_data['dataframe'] = [
                    {k: clean_value(v) for k, v in row.items()}
                    for row in df_dict
                ]
                export_data['export_info']['data_shape'] = {
                    'rows': data.dataframe.shape[0],
                    'columns': data.dataframe.shape[1],
                    'column_names': list(data.dataframe.columns)
                }
            
            # 导出属性（只导出非None值）
            export_data['attributes'] = {
                k: v for k, v in data.attributes.items() if v is not None
            }
            
            # 导出扩展属性
            export_data['extra_attributes'] = dict(data.extra_attributes)
            
            # 写入JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=indent, ensure_ascii=False)
            
            print(f"✅ 数据已导出到JSON: {file_path}")
            return True, None
            
        except PermissionError:
            return False, f"文件被占用或无权限写入:\n{file_path}\n\n请关闭该文件后重试"
        except Exception as e:
            return False, f"导出JSON时发生错误:\n{str(e)}"
    
    @staticmethod
    def get_default_export_dir() -> Path:
        """
        获取默认导出目录（项目根目录/exports）
        
        返回:
            Path对象
        """
        # 获取项目根目录
        import os
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # src/utils -> src -> root
        export_dir = project_root / 'exports'
        
        # 确保目录存在
        export_dir.mkdir(exist_ok=True)
        
        return export_dir
    
    @staticmethod
    def get_default_filename(data, format_ext: str) -> str:
        """
        生成默认文件名
        
        参数:
            data: Data对象
            format_ext: 格式扩展名（'xlsx', 'csv', 'json'）
        
        返回:
            文件名（不含路径）
        """
        # 清理数据名称
        clean_name = DataExporter.sanitize_filename(data.name)
        
        # 添加时间戳（避免覆盖）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 组合文件名
        filename = f"{clean_name}_{timestamp}.{format_ext}"
        
        return filename

