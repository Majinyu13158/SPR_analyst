# -*- coding: utf-8 -*-
"""
数据模型 - 融合版
支持：
1. 原项目的25个详细属性（SPR实验数据）
2. DataFrame数据存储和处理
3. 智能XY数据提取
4. 可扩展的额外属性
"""
from typing import Dict, Optional, Any, Tuple
from PySide6.QtCore import QObject, Signal
import pandas as pd
import numpy as np


class Data(QObject):
    """
    统一数据类 - 融合原项目和新项目的所有优点
    
    支持两种创建方式：
    1. 从JSON文件：包含完整的SPR实验属性
    2. 从DataFrame：用于拟合结果或手动创建的数据
    """
    # 信号：数据更新时触发
    data_updated = Signal()
    
    def __init__(self, item=None, itemtype: str = 'dataframe', parent=None):
        """
        初始化数据对象
        
        参数:
            item: 数据源（Dict for JSON, DataFrame for dataframe, etc.）
            itemtype: 数据类型 ('file', 'fitting', 'dataframe')
            parent: Qt父对象
        """
        super().__init__(parent)
        
        # ===== 基本信息 =====
        self.name: str = "未命名数据"
        self.itemtype: str = itemtype
        self.connection_id: Optional[int] = None
        
        # ===== 数据存储 =====
        self.dataframe: pd.DataFrame = pd.DataFrame()  # 统一用DataFrame存储
        self.raw_data: Dict = {}  # 原始JSON数据（如果有）
        
        # ===== 25个默认属性（SPR实验数据专用）=====
        self.attributes: Dict[str, Any] = {
            # 全局设置（7个）
            'cauculatedatasource': None,
            'calculatedatatype': None,
            'fittingformula': None,
            'fittingoptions_kdbound': None,
            'fittingoptions_punishupper': None,
            'fittingoptions_punishlower': None,
            'fittingoptions_punishk': None,
            # 样本属性（18个）
            'calculatedatalist_experimentid': None,
            'calculatedatalist_sampleid': None,
            'calculatedatalist_molecular': None,
            'calculatedatalist_samplename': None,
            'calculatedatalist_concentration': None,
            'calculatedatalist_concentrationunit': None,
            'calculatedatalist_holetype': None,
            'basestaryindex': None,
            'calculatedatalist_combinestartindex': None,
            'calculatedatalist_combineendindex': None,
            'calculatedatalist_dissociationendindex': None,
            'ligandfixationdata': None,
            'ligandstabilitydata': None,
        }
        
        # ===== 可扩展属性（非默认字段） =====
        self.extra_attributes: Dict[str, Any] = {}
        
        # 根据类型初始化
        if item is not None:
            if itemtype == 'file':
                self._load_from_file(item)
            elif itemtype == 'fitting':
                self._load_from_fitting(item)
            elif itemtype == 'dataframe':
                self._load_from_dataframe(item)
    
    def _load_from_file(self, data: Dict):
        """
        从JSON文件加载（原项目风格）
        
        自动提取：
        1. 25个默认属性 → self.attributes
        2. BaseData → self.dataframe
        3. 其他未知字段 → self.extra_attributes
        """
        self.raw_data = data
        
        try:
            # 提取全局设置
            self.attributes['cauculatedatasource'] = data.get('CalculateDataSource')
            self.attributes['calculatedatatype'] = data.get('CalculateDataType')
            self.attributes['fittingformula'] = data.get('CalculateFormula')
            
            # 提取FittingOptions（可能是嵌套字典或平铺）
            if 'FittingOptions' in data and isinstance(data['FittingOptions'], dict):
                self.attributes['fittingoptions_kdbound'] = data['FittingOptions'].get('KDBound')
                self.attributes['fittingoptions_punishupper'] = data['FittingOptions'].get('PunishUpper')
                self.attributes['fittingoptions_punishlower'] = data['FittingOptions'].get('PunishLower')
                self.attributes['fittingoptions_punishk'] = data['FittingOptions'].get('PunishK')
            else:
                # 平铺格式
                self.attributes['fittingoptions_kdbound'] = data.get('FittingOptions_KDBound')
                self.attributes['fittingoptions_punishupper'] = data.get('FittingOptions_PunishUpper')
                self.attributes['fittingoptions_punishlower'] = data.get('FittingOptions_PunishLower')
                self.attributes['fittingoptions_punishk'] = data.get('FittingOptions_PunishK')
            
            # 提取CalculateDataList中的样本信息
            if 'CalculateDataList' in data and len(data['CalculateDataList']) > 0:
                samples = data['CalculateDataList']
                first_item = samples[0]
                
                # 样本基本信息（从第一个样本提取）
                self.attributes['calculatedatalist_experimentid'] = first_item.get('ExperimentID')
                self.attributes['calculatedatalist_sampleid'] = first_item.get('SampleID')
                self.attributes['calculatedatalist_molecular'] = first_item.get('Molecular')
                self.attributes['calculatedatalist_samplename'] = first_item.get('SampleName')
                self.attributes['calculatedatalist_concentration'] = first_item.get('Concentration')
                self.attributes['calculatedatalist_concentrationunit'] = first_item.get('ConcentrationUnit')
                self.attributes['calculatedatalist_holetype'] = first_item.get('HoleType')
                
                # 索引信息
                self.attributes['basestaryindex'] = first_item.get('BaseStartIndex')
                self.attributes['calculatedatalist_combinestartindex'] = first_item.get('CombineStartIndex')
                self.attributes['calculatedatalist_combineendindex'] = first_item.get('CombineEndIndex')
                self.attributes['calculatedatalist_dissociationendindex'] = first_item.get('DissociationEndIndex')
                
                # 配体数据（从列表末尾提取，如果存在）
                if len(samples) >= 3:
                    self.attributes['ligandfixationdata'] = samples[-2].get('LigandFixationData')
                    self.attributes['ligandstabilitydata'] = samples[-1].get('LigandStabilityData')
                
                # ⭐ 关键改进：检测多样本数据
                if len(samples) > 1:
                    # 多浓度数据 → 构建宽表（Time | 浓度1 | 浓度2 | ...）
                    self.dataframe = self._build_wide_table_from_samples(samples)
                    sample_name = self.attributes['calculatedatalist_samplename'] or "未命名数据"
                    self.name = f"{sample_name} ({len(samples)}浓度)"
                    print(f"✅ 从JSON加载多浓度数据: {len(samples)}个样本 → 宽表 ({self.name})")
                else:
                    # 单样本数据 → 直接转DataFrame
                    base_data = first_item.get('BaseData', [])
                    if base_data:
                        self.dataframe = pd.DataFrame(base_data)
                        self.name = self.attributes['calculatedatalist_samplename'] or "未命名数据"
                        print(f"✅ 从JSON加载单样本数据: {len(base_data)}行 → DataFrame ({self.name})")
            
            # 提取其他未知字段到extra_attributes
            known_keys = {'CalculateDataSource', 'CalculateDataType', 'CalculateFormula', 
                         'FittingOptions', 'FittingOptions_KDBound', 'FittingOptions_PunishUpper',
                         'FittingOptions_PunishLower', 'FittingOptions_PunishK', 'CalculateDataList'}
            for key, value in data.items():
                if key not in known_keys:
                    self.extra_attributes[key] = value
                    
        except Exception as e:
            print(f"⚠️ JSON加载警告: {e}")
            # 即使部分失败，也保留已提取的数据
    
    def _build_wide_table_from_samples(self, samples: list) -> pd.DataFrame:
        """
        从多个样本构建宽表（用于LocalBivariate）
        
        输入：samples列表，每个样本包含Concentration和BaseData/CombineData/DissociationData
        输出：宽表DataFrame
            Time | 浓度1 | 浓度2 | ... | 浓度N
            0.0  | Y1    | Y2    | ... | YN
            1.0  | Y1    | Y2    | ... | YN
            ...
        
        参数:
            samples: CalculateDataList数组
        
        返回:
            宽表DataFrame
        """
        import numpy as np
        
        # ⭐ 合并所有数据点（BaseData + CombineData + DissociationData）
        def get_all_data_from_sample(sample):
            """从样本中合并所有数据点"""
            all_data = []
            if 'BaseData' in sample and sample['BaseData']:
                all_data.extend(sample['BaseData'])
            if 'CombineData' in sample and sample['CombineData']:
                all_data.extend(sample['CombineData'])
            if 'DissociationData' in sample and sample['DissociationData']:
                all_data.extend(sample['DissociationData'])
            return all_data
        
        # 提取时间点（从第一个样本）
        first_all_data = get_all_data_from_sample(samples[0])
        if not first_all_data:
            print("⚠️ 第一个样本没有数据")
            return pd.DataFrame()
        
        # 提取时间列（XValue就是时间！）
        time_values = [d.get('XValue', d.get('Time', 0)) for d in first_all_data]
        
        print(f"[Data Model] 合并数据点: BaseData + CombineData + DissociationData = {len(time_values)}点")
        print(f"[Data Model] 时间范围: {min(time_values)} ~ {max(time_values)}")
        
        # 构建字典：Time列 + 各浓度列
        wide_data = {'Time': time_values}
        
        # 遍历每个样本，提取浓度和Y值
        for sample in samples:
            concentration = sample.get('Concentration', 0.0)
            
            # ⭐ 获取所有数据点（合并Base+Combine+Dissociation）
            all_data = get_all_data_from_sample(sample)
            
            # 提取Y值
            y_values = [d.get('YValue', 0.0) for d in all_data]
            
            # 检查长度一致性
            if len(y_values) != len(time_values):
                print(f"⚠️ 警告：浓度{concentration}的数据点数({len(y_values)})与时间点数({len(time_values)})不一致")
                # 补齐或截断
                if len(y_values) < len(time_values):
                    y_values.extend([np.nan] * (len(time_values) - len(y_values)))
                else:
                    y_values = y_values[:len(time_values)]
            
            # 使用浓度值作为列名
            col_name = str(concentration)
            wide_data[col_name] = y_values
        
        df = pd.DataFrame(wide_data)
        
        print(f"✅ 构建宽表: {len(time_values)}时间点 × {len(samples)}浓度")
        print(f"   列名: {list(df.columns)}")
        print(f"   DataFrame形状: {df.shape}")
        
        return df
    
    def _load_from_fitting(self, data: Any):
        """从拟合结果加载"""
        if isinstance(data, pd.DataFrame):
            self.dataframe = data.copy()
        else:
            self.dataframe = pd.DataFrame(data)
        self.name = "拟合结果"
        print(f"✅ 从拟合结果加载 {len(self.dataframe)} 行数据")
    
    def _load_from_dataframe(self, data: Any):
        """从DataFrame或字典加载"""
        if isinstance(data, pd.DataFrame):
            self.dataframe = data.copy()
        elif isinstance(data, dict):
            self.dataframe = pd.DataFrame(data)
        else:
            self.dataframe = pd.DataFrame()
        print(f"✅ 从DataFrame加载 {len(self.dataframe)} 行数据")
    
    # ===== 属性访问方法（统一接口） =====
    
    def set_attribute(self, key: str, value: Any):
        """
        设置属性（自动判断是默认属性还是扩展属性）
        
        参数:
            key: 属性名
            value: 属性值
        """
        if key in self.attributes:
            self.attributes[key] = value
        else:
            self.extra_attributes[key] = value
    
    def get_attribute(self, key: str, default=None) -> Any:
        """
        获取属性（统一接口）
        
        参数:
            key: 属性名
            default: 默认值（如果属性不存在）
        
        返回:
            属性值
        """
        if key in self.attributes:
            return self.attributes[key]
        return self.extra_attributes.get(key, default)
    
    # ===== 数据访问方法 =====
    
    def get_processed_data(self) -> pd.DataFrame:
        """获取处理后的数据（DataFrame格式）"""
        return self.dataframe
    
    def get_name(self) -> str:
        """获取数据名称"""
        return self.name
    
    def set_name(self, name: str):
        """设置数据名称"""
        self.name = name
    
    # ===== 智能XY提取（新项目的核心功能） =====
    
    def get_xy_data(
        self,
        x_col: Optional[str] = None,
        y_col: Optional[str] = None,
        auto_sort: bool = True,
        drop_na: bool = True,
        return_info: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        提取X和Y数据（智能选择或手动指定）
        
        功能：
        - 宽松解析字符串为数值（单位/逗号小数/科学计数法）
        - 智能选择：X优先 Time/XValue；Y优先 Response/RU/YValue
        - 排除明显的元数据列（Concentration/Index/ID 等）
        - 可选：按X排序、删除NaN
        
        参数:
            x_col: 手动指定X列名（None=自动智能选择）
            y_col: 手动指定Y列名（None=自动智能选择）
            auto_sort: 是否按X排序（默认True，绘图用；False保持原顺序，拟合用）
            drop_na: 是否删除NaN（默认True；False保留NaN，适用于某些算法）
            return_info: 是否返回提取信息（用于调试和验证）
        
        返回:
            (x_data, y_data): numpy数组元组
            如果 return_info=True: (x_data, y_data, info_dict)
        
        异常:
            ValueError: 数据为空、列不存在、无有效数据点等
        
        示例:
            # 智能提取（绘图用）
            x, y = data.get_xy_data()
            
            # 手动指定列（拟合用）
            x, y = data.get_xy_data(x_col='Time', y_col='Response', auto_sort=False)
            
            # 获取详细信息
            x, y, info = data.get_xy_data(return_info=True)
            print(f"选择的列: {info['x_col']}, {info['y_col']}")
        """
        import re
        
        df = self.dataframe
        if df is None or df.empty:
            raise ValueError("数据为空")

        def parse_numeric_series(s: pd.Series) -> pd.Series:
            """更宽松的数值解析：
            - 允许字符串中带单位（提取首个数字片段）
            - 支持逗号作为小数点或千分位，做合理替换
            - 支持科学计数法
            返回float系列（不可转的为NaN）
            """
            if s.dtype.kind in ('i', 'u', 'f'):
                return pd.to_numeric(s, errors='coerce')
            # 转为字符串处理
            s_str = s.astype(str).str.strip()

            # 先把常见千分位和小数点情况做预处理：
            # 情况A: "1,234.56" → 去掉千分位逗号
            s_norm = s_str.str.replace(r"(?<=\d),(?=\d{3}(\D|$))", "", regex=True)
            # 情况B: "1.234,56" → 先把点去掉，再把逗号当小数点
            s_norm = s_norm.str.replace(r"(\d)\.(?=\d{3}(\D|$))", r"\1", regex=True)
            s_norm = s_norm.str.replace(",", ".", regex=False)

            # 提取第一个数字（含可选小数与科学计数法）
            num_pat = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
            def extract_first_number(text: str) -> float:
                m = num_pat.search(text)
                if not m:
                    return float('nan')
                try:
                    return float(m.group(0))
                except Exception:
                    return float('nan')

            parsed = s_norm.map(extract_first_number)
            return pd.to_numeric(parsed, errors='coerce')

        # 为所有列准备"可解析为数值"的统计
        numeric_map = {}
        valid_counts = {}
        for col in df.columns:
            ser = parse_numeric_series(df[col])
            numeric_map[col] = ser
            valid_counts[col] = int(ser.notna().sum())

        if not valid_counts:
            raise ValueError("没有可用的列")

        # ===== 选择X列（手动指定 或 智能选择）=====
        selected_x_col = x_col
        if selected_x_col is None:
            # 智能选择X列
            preferred_x = ['Time', 'time', 'XValue', 'X', 'x', 't', 'sec', 'seconds']
            existing_pref = [c for c in preferred_x if c in df.columns]
            # 在偏好列中选择有效点最多的
            if existing_pref:
                selected_x_col = max(existing_pref, key=lambda c: valid_counts.get(c, 0))
            # 若偏好列几乎无效，则在所有列中选有效点最多者
            if selected_x_col is None or valid_counts.get(selected_x_col, 0) == 0:
                selected_x_col = max(valid_counts, key=valid_counts.get)
        else:
            # 验证手动指定的X列
            if selected_x_col not in df.columns:
                raise ValueError(f"指定的X列不存在: '{selected_x_col}'，可用列: {list(df.columns)}")
            if valid_counts.get(selected_x_col, 0) == 0:
                raise ValueError(f"指定的X列无有效数值: '{selected_x_col}'")
        
        if valid_counts.get(selected_x_col, 0) == 0:
            raise ValueError(f"X列无有效数值。列: {list(df.columns)}")

        # ===== 选择Y列（手动指定 或 智能选择）=====
        selected_y_col = y_col
        stats = {}  # 用于存储统计信息
        y_candidates = []  # 候选Y列列表
        
        if selected_y_col is None:
            # 智能选择Y列
            preferred_y = ['Response', 'response', 'RU', 'YValue', 'y', 'signal', 'Signal', 'Value']
            blacklist = set(['Concentration', 'concentration', 'Index', 'index', 'ID', 'id', 'Cycle', 'Group', 'Sample', 'Run', 'Replicate'])

            # 先构造所有候选（排除X和黑名单，且有效点>0）
            candidates = [
                c for c, cnt in valid_counts.items()
                if c != selected_x_col and cnt > 0 and c not in blacklist
            ]
            if not candidates:
                raise ValueError("未找到可用的Y列（除X外）")

            # 计算变化性（std、unique）
            for c in candidates:
                s = numeric_map[c].dropna()
                stats[c] = dict(std=float(s.std()) if not s.empty else 0.0,
                                uniq=int(s.nunique()))

            def score(col: str) -> tuple:
                # 评分：是否在首选列表(-0/1)、有效点数、多样性、标准差
                pref = 0 if col in preferred_y else 1
                return (
                    pref,
                    -valid_counts[col],
                    -stats[col]['uniq'],
                    -stats[col]['std']
                )

            # 过滤掉"无变化"的列（std==0 或 uniq<=3）
            filtered = [c for c in candidates if stats[c]['std'] > 0 and stats[c]['uniq'] > 3]
            if not filtered:
                # 退化：没有满足变化性，仍挑评分最高者
                filtered = candidates

            selected_y_col = sorted(filtered, key=score)[0]
            y_candidates = candidates  # 保存候选列表供info使用
        else:
            # 验证手动指定的Y列
            if selected_y_col not in df.columns:
                raise ValueError(f"指定的Y列不存在: '{selected_y_col}'，可用列: {list(df.columns)}")
            if valid_counts.get(selected_y_col, 0) == 0:
                raise ValueError(f"指定的Y列无有效数值: '{selected_y_col}'")
            # 计算该列的统计信息
            s = numeric_map[selected_y_col].dropna()
            stats[selected_y_col] = dict(std=float(s.std()) if not s.empty else 0.0,
                                         uniq=int(s.nunique()))

        # ===== 提取数据 =====
        x_series = numeric_map[selected_x_col]
        y_series = numeric_map[selected_y_col]
        
        if drop_na:
            # 删除NaN（对齐有效数据）
            mask = x_series.notna() & y_series.notna()
            x_valid = x_series[mask].to_numpy(dtype=float)
            y_valid = y_series[mask].to_numpy(dtype=float)
            original_indices = np.where(mask)[0]
        else:
            # 保留NaN
            x_valid = x_series.to_numpy(dtype=float)
            y_valid = y_series.to_numpy(dtype=float)
            original_indices = np.arange(len(x_valid))

        if x_valid.size == 0 or y_valid.size == 0:
            raise ValueError("有效数据点为0，无法处理")

        # ===== 排序（可选）=====
        if auto_sort:
            # 按X排序，避免来回折线
            order = np.argsort(x_valid)
            x_data = x_valid[order]
            y_data = y_valid[order]
            sorted_indices = original_indices[order]
        else:
            # 保持原始顺序
            x_data = x_valid
            y_data = y_valid
            sorted_indices = original_indices

        # ===== 调试信息 =====
        mode_str = "手动" if (x_col or y_col) else "智能"
        print(f"[Data.get_xy_data] 模式={mode_str}, X={selected_x_col}({valid_counts.get(selected_x_col)}点), Y={selected_y_col}({valid_counts.get(selected_y_col)}点), 有效={x_data.size}点, 排序={auto_sort}, NaN过滤={drop_na}")
        
        # ===== 返回结果 =====
        if return_info:
            # 返回详细信息
            info = {
                'x_col': selected_x_col,
                'y_col': selected_y_col,
                'total_points': len(df),
                'valid_points': x_data.size,
                'dropped_na': len(df) - x_data.size if drop_na else 0,
                'is_sorted': auto_sort,
                'mode': mode_str,
                'y_candidates': y_candidates if not y_col else [],
                'statistics': stats.get(selected_y_col, {}),
                'indices': sorted_indices  # 数据点在原DataFrame中的索引
            }
            return x_data, y_data, info
        else:
            return x_data, y_data

    def validate_xy_extraction(
        self,
        x_col: Optional[str] = None,
        y_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        验证XY提取（不实际提取数据，仅返回会提取什么）
        
        用途：
        - 在拟合前检查数据选择是否正确
        - 提供备选列列表供用户选择
        - 检测潜在问题（数据点过少、NaN过多等）
        
        参数:
            x_col: 指定X列（None=自动选择）
            y_col: 指定Y列（None=自动选择）
        
        返回:
            {
                'x_col': 'Time',           # 将使用的X列
                'y_col': 'Response',       # 将使用的Y列
                'total_points': 100,       # DataFrame总行数
                'valid_x_points': 98,      # X列有效点数
                'valid_y_points': 95,      # Y列有效点数
                'valid_both': 93,          # X和Y都有效的点数
                'na_count': 7,             # 缺失值数量
                'warnings': [...],         # 警告列表
                'y_candidates': [...],     # 其他可选Y列
                'columns_info': {...}      # 所有列的详细信息
            }
        
        示例:
            # 验证智能选择结果
            result = data.validate_xy_extraction()
            if result['warnings']:
                print("警告:", result['warnings'])
            print(f"将使用: X={result['x_col']}, Y={result['y_col']}")
            
            # 验证手动指定的列
            result = data.validate_xy_extraction(x_col='Time', y_col='Response')
            if result['valid_both'] < 10:
                print("数据点太少！")
        """
        df = self.dataframe
        if df is None or df.empty:
            return {
                'error': '数据为空',
                'warnings': ['DataFrame为空或未初始化']
            }
        
        # 准备数值解析（复用get_xy_data的逻辑）
        import re
        
        def parse_numeric_series(s: pd.Series) -> pd.Series:
            if s.dtype.kind in ('i', 'u', 'f'):
                return pd.to_numeric(s, errors='coerce')
            s_str = s.astype(str).str.strip()
            s_norm = s_str.str.replace(r"(?<=\d),(?=\d{3}(\D|$))", "", regex=True)
            s_norm = s_norm.str.replace(r"(\d)\.(?=\d{3}(\D|$))", r"\1", regex=True)
            s_norm = s_norm.str.replace(",", ".", regex=False)
            num_pat = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
            def extract_first_number(text: str) -> float:
                m = num_pat.search(text)
                if not m:
                    return float('nan')
                try:
                    return float(m.group(0))
                except Exception:
                    return float('nan')
            parsed = s_norm.map(extract_first_number)
            return pd.to_numeric(parsed, errors='coerce')
        
        # 为所有列准备统计信息
        numeric_map = {}
        valid_counts = {}
        columns_info = {}
        
        for col in df.columns:
            ser = parse_numeric_series(df[col])
            numeric_map[col] = ser
            valid_count = int(ser.notna().sum())
            valid_counts[col] = valid_count
            
            # 详细列信息
            columns_info[col] = {
                'dtype': str(df[col].dtype),
                'total': len(df),
                'valid': valid_count,
                'na_count': len(df) - valid_count,
                'mean': float(ser.mean()) if valid_count > 0 else None,
                'std': float(ser.std()) if valid_count > 0 else None,
                'min': float(ser.min()) if valid_count > 0 else None,
                'max': float(ser.max()) if valid_count > 0 else None,
                'unique': int(ser.nunique())
            }
        
        # 选择X列（与get_xy_data逻辑一致）
        selected_x_col = x_col
        if selected_x_col is None:
            preferred_x = ['Time', 'time', 'XValue', 'X', 'x', 't', 'sec', 'seconds']
            existing_pref = [c for c in preferred_x if c in df.columns]
            if existing_pref:
                selected_x_col = max(existing_pref, key=lambda c: valid_counts.get(c, 0))
            if selected_x_col is None or valid_counts.get(selected_x_col, 0) == 0:
                selected_x_col = max(valid_counts, key=valid_counts.get) if valid_counts else None
        
        # 选择Y列（与get_xy_data逻辑一致）
        selected_y_col = y_col
        y_candidates = []
        
        if selected_y_col is None:
            preferred_y = ['Response', 'response', 'RU', 'YValue', 'y', 'signal', 'Signal', 'Value']
            blacklist = set(['Concentration', 'concentration', 'Index', 'index', 'ID', 'id', 'Cycle', 'Group', 'Sample', 'Run', 'Replicate'])
            
            candidates = [
                c for c, cnt in valid_counts.items()
                if c != selected_x_col and cnt > 0 and c not in blacklist
            ]
            
            if candidates:
                # 计算统计并排序
                stats = {}
                for c in candidates:
                    s = numeric_map[c].dropna()
                    stats[c] = dict(
                        std=float(s.std()) if not s.empty else 0.0,
                        uniq=int(s.nunique())
                    )
                
                def score(col: str) -> tuple:
                    pref = 0 if col in preferred_y else 1
                    return (pref, -valid_counts[col], -stats[col]['uniq'], -stats[col]['std'])
                
                filtered = [c for c in candidates if stats[c]['std'] > 0 and stats[c]['uniq'] > 3]
                if not filtered:
                    filtered = candidates
                
                selected_y_col = sorted(filtered, key=score)[0]
                y_candidates = candidates  # 所有候选
        
        # 计算有效数据点
        if selected_x_col and selected_y_col:
            x_series = numeric_map[selected_x_col]
            y_series = numeric_map[selected_y_col]
            valid_both = int((x_series.notna() & y_series.notna()).sum())
        else:
            valid_both = 0
        
        # 生成警告
        warnings = []
        if selected_x_col is None:
            warnings.append("未找到合适的X列")
        elif valid_counts.get(selected_x_col, 0) < len(df) * 0.5:
            warnings.append(f"X列'{selected_x_col}'缺失值较多（{len(df) - valid_counts.get(selected_x_col, 0)}个）")
        
        if selected_y_col is None:
            warnings.append("未找到合适的Y列")
        elif valid_counts.get(selected_y_col, 0) < len(df) * 0.5:
            warnings.append(f"Y列'{selected_y_col}'缺失值较多（{len(df) - valid_counts.get(selected_y_col, 0)}个）")
        
        if valid_both < 3:
            warnings.append(f"有效数据点过少（仅{valid_both}个），拟合可能失败")
        elif valid_both < 10:
            warnings.append(f"有效数据点较少（{valid_both}个），拟合精度可能不高")
        
        na_count = len(df) - valid_both if valid_both > 0 else len(df)
        if na_count > 0:
            warnings.append(f"将过滤{na_count}个数据点（NaN或无效值）")
        
        if len(y_candidates) > 1:
            warnings.append(f"存在{len(y_candidates)}个候选Y列，请确认选择正确")
        
        # 返回结果
        return {
            'x_col': selected_x_col,
            'y_col': selected_y_col,
            'total_points': len(df),
            'valid_x_points': valid_counts.get(selected_x_col, 0) if selected_x_col else 0,
            'valid_y_points': valid_counts.get(selected_y_col, 0) if selected_y_col else 0,
            'valid_both': valid_both,
            'na_count': na_count,
            'warnings': warnings,
            'y_candidates': y_candidates,
            'columns_info': columns_info,
            'mode': '手动指定' if (x_col or y_col) else '智能选择'
        }


class DataManager(QObject):
    """
    数据管理器 - 统一接口管理所有数据对象
    
    支持多种数据添加方式，自动创建合适的Data对象
    """
    # 信号
    data_added = Signal(int)  # 参数：数据ID
    data_removed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_dict: Dict[int, Data] = {}
        self._counter: int = 0
    
    def add_data(self, name_or_item=None, dataframe_or_type=None, **kwargs) -> int:
        """
        添加新数据（智能接口，自动识别参数类型）
        
        用法1 - 从DataFrame创建（位置参数）：
            add_data("样本A", df) -> int
            
        用法2 - 从DataFrame创建（关键字参数）：
            add_data(name="样本A", dataframe=df) -> int
            
        用法3 - 从JSON字典创建：
            add_data(json_dict, 'file') -> int
            add_data(item=json_dict, itemtype='file') -> int
        
        参数:
            name_or_item: 数据名称(str) 或 JSON字典(Dict)
            dataframe_or_type: DataFrame对象 或 数据类型('file'/'fitting')
            **kwargs: 支持关键字参数 name, dataframe, item, itemtype
        
        返回:
            int: 分配的数据ID
        """
        # 处理关键字参数（优先级更高）
        if 'name' in kwargs or 'dataframe' in kwargs:
            # 关键字参数方式：add_data(name="样本A", dataframe=df)
            name = kwargs.get('name', name_or_item)
            dataframe = kwargs.get('dataframe', dataframe_or_type)
            
            if name is None:
                raise ValueError("必须提供 name 参数")
            
            # 创建Data对象（dataframe类型）
            data = Data(item=dataframe, itemtype='dataframe', parent=self)
            data.set_name(name)
            
        elif 'item' in kwargs or 'itemtype' in kwargs:
            # 关键字参数方式：add_data(item=json_dict, itemtype='file')
            item = kwargs.get('item', name_or_item)
            itemtype = kwargs.get('itemtype', dataframe_or_type if dataframe_or_type else 'file')
            
            if item is None:
                raise ValueError("必须提供 item 参数")
            
            # 创建Data对象（file/fitting类型）
            data = Data(item=item, itemtype=itemtype, parent=self)
            
        # 位置参数方式（智能判断类型）
        elif isinstance(name_or_item, str):
            # ===== 接口1：从DataFrame创建 =====
            name = name_or_item
            dataframe = dataframe_or_type
            
            # 创建Data对象（dataframe类型）
            data = Data(item=dataframe, itemtype='dataframe', parent=self)
            data.set_name(name)
            
        elif isinstance(name_or_item, dict):
            # ===== 接口2：从JSON创建 =====
            item = name_or_item
            itemtype = dataframe_or_type if dataframe_or_type else 'file'
            
            # 创建Data对象（file/fitting类型）
            data = Data(item=item, itemtype=itemtype, parent=self)
            
        else:
            raise TypeError(f"不支持的参数类型或缺少必需参数。请使用：\n"
                          f"  - add_data('name', df)\n"
                          f"  - add_data(name='name', dataframe=df)\n"
                          f"  - add_data(json_dict, 'file')\n"
                          f"收到: name_or_item={type(name_or_item)}, kwargs={kwargs}")
        
        # 分配ID并存储
        data_id = self._counter
        self._data_dict[data_id] = data
        self._counter += 1
        
        # 发射信号
        self.data_added.emit(data_id)
        
        print(f"✅ 数据已添加到DataManager: ID={data_id}, Name={data.get_name()}, Type={data.itemtype}")
        
        return data_id
    
    def get_data(self, data_id: int) -> Optional[Data]:
        """
        获取指定ID的数据对象
        
        参数:
            data_id: 数据ID
        
        返回:
            Data对象 或 None（如果ID不存在）
        """
        return self._data_dict.get(data_id)
    
    def remove_data(self, data_id: int) -> bool:
        """
        删除指定ID的数据
        
        参数:
            data_id: 数据ID
        
        返回:
            bool: 是否删除成功
        """
        if data_id in self._data_dict:
            del self._data_dict[data_id]
            self.data_removed.emit(data_id)
            print(f"✅ 数据已删除: ID={data_id}")
            return True
        return False
    
    def get_all_data(self) -> Dict[int, Data]:
        """
        获取所有数据对象
        
        返回:
            Dict[int, Data]: 数据ID → Data对象的字典
        """
        return self._data_dict.copy()
    
    def get_data_count(self) -> int:
        """获取数据数量"""
        return len(self._data_dict)
    
    def clear_all(self):
        """清空所有数据"""
        data_ids = list(self._data_dict.keys())
        for data_id in data_ids:
            self.remove_data(data_id)
        print("✅ 所有数据已清空")

