# -*- coding: utf-8 -*-
"""
数据模型 - 管理SPR实验数据（MVP简化版）
"""
from typing import Dict, Optional, Any
from PySide6.QtCore import QObject, Signal
import pandas as pd


class DataSimple(QObject):
    """
    简化数据类（新接口专用）
    
    用于新接口：add_data(name, dataframe)
    """
    data_updated = Signal()
    
    def __init__(self, name: str, dataframe: Optional[pd.DataFrame] = None, parent=None):
        super().__init__(parent)
        self.name = name
        self.dataframe = dataframe if dataframe is not None else pd.DataFrame()
        self.attributes: Dict[str, Any] = {}
    
    def get_processed_data(self) -> pd.DataFrame:
        """获取处理后的数据"""
        return self.dataframe
    
    def get_name(self) -> str:
        """获取数据名称"""
        return self.name
    
    def get_xy_data(self):
        """
        提取X和Y数据用于绘图（更强鲁棒性 + 语义优先 + 变化性约束）：
        - 宽松解析字符串为数值（单位/逗号小数/科学计数法）
        - X优先 Time/XValue/常见时间列；Y优先 Response/RU/YValue 等
        - 排除明显的元数据列（Concentration/Index/ID 等）
        - 仅选择“有变化”的Y（std>0、unique>3），并按X排序
        - 返回等长float数组
        """
        import re
        import numpy as np
        import pandas as pd
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

        # 为所有列准备“可解析为数值”的统计
        numeric_map = {}
        valid_counts = {}
        for col in df.columns:
            ser = parse_numeric_series(df[col])
            numeric_map[col] = ser
            valid_counts[col] = int(ser.notna().sum())

        if not valid_counts:
            raise ValueError("没有可用的列")

        # 候选X列（按偏好排序，如果均无效则按有效点最多选择）
        preferred_x = ['Time', 'time', 'XValue', 'X', 'x', 't', 'sec', 'seconds']
        existing_pref = [c for c in preferred_x if c in df.columns]
        # 在偏好列中选择有效点最多的
        x_col = None
        if existing_pref:
            x_col = max(existing_pref, key=lambda c: valid_counts.get(c, 0))
        # 若偏好列几乎无效，则在所有列中选有效点最多者
        if x_col is None or valid_counts.get(x_col, 0) == 0:
            x_col = max(valid_counts, key=valid_counts.get)
        if valid_counts.get(x_col, 0) == 0:
            raise ValueError(f"X列无有效数值。列: {list(df.columns)}")

        # 选择Y列（语义优先 + 变化性约束）
        preferred_y = ['Response', 'response', 'RU', 'YValue', 'y', 'signal', 'Signal', 'Value']
        blacklist = set(['Concentration', 'concentration', 'Index', 'index', 'ID', 'id', 'Cycle', 'Group', 'Sample', 'Run', 'Replicate'])

        # 先构造所有候选（排除X和黑名单，且有效点>0）
        candidates = [
            c for c, cnt in valid_counts.items()
            if c != x_col and cnt > 0 and c not in blacklist
        ]
        if not candidates:
            raise ValueError("未找到可用的Y列（除X外）")

        # 计算变化性（std、unique）
        stats = {}
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

        # 过滤掉“无变化”的列（std==0 或 uniq<=3）
        filtered = [c for c in candidates if stats[c]['std'] > 0 and stats[c]['uniq'] > 3]
        if not filtered:
            # 退化：没有满足变化性，仍挑评分最高者
            filtered = candidates

        y_col = sorted(filtered, key=score)[0]

        # 对齐有效数据并按X排序
        x_series = numeric_map[x_col]
        y_series = numeric_map[y_col]
        mask = x_series.notna() & y_series.notna()
        x_valid = x_series[mask].to_numpy(dtype=float)
        y_valid = y_series[mask].to_numpy(dtype=float)

        if x_valid.size == 0 or y_valid.size == 0:
            raise ValueError("有效数据点为0，无法绘图")

        # 按X排序，避免来回折线或看似“直线”错觉
        order = np.argsort(x_valid)
        x_data = x_valid[order]
        y_data = y_valid[order]

        # 调试信息（便于定位）
        print(f"[DataSimple.get_xy_data] X={x_col}({valid_counts.get(x_col)}), Y={y_col}({valid_counts.get(y_col)}), uniqY={stats.get(y_col,{}).get('uniq','?')}, stdY={stats.get(y_col,{}).get('std','?'):.6f}, N={x_data.size}")
        return x_data, y_data


class Data(QObject):
    """
    单个数据集类 - MVP简化版（旧接口专用）
    
    只保留最基本的数据管理功能
    """
    # 信号：数据更新时触发
    data_updated = Signal()
    
    def __init__(self, item: Dict, itemtype: str, parent=None):
        super().__init__(parent)
        self.connection_id: Optional[int] = None
        self.itemtype = itemtype
        self.name = "未命名数据"
        self.dataframe: Optional[pd.DataFrame] = None  # 添加dataframe属性以保持一致性
        
        # 简化的属性存储
        self.attributes: Dict[str, Any] = {}
        self.raw_data: Dict = {}
        self.processed_data: pd.DataFrame = pd.DataFrame()
        
        # 根据类型初始化
        if itemtype == 'file':
            self._load_from_file(item)
        elif itemtype == 'fitting':
            self._load_from_fitting(item)
        
        # 同步dataframe属性
        self.dataframe = self.processed_data
    
    def _load_from_file(self, data: Dict):
        """从文件数据加载 - MVP简化版"""
        self.raw_data = data
        
        # 提取关键信息
        if 'CalculateDataList' in data and len(data['CalculateDataList']) > 0:
            first_item = data['CalculateDataList'][0]
            self.name = first_item.get('SampleName', '未命名数据')
            self.attributes['sample_name'] = self.name
            self.attributes['concentration'] = first_item.get('Concentration')
            
            # 提取BaseData并转换为DataFrame
            base_data = first_item.get('BaseData', [])
            if base_data:
                self.processed_data = pd.DataFrame(base_data)
    
    def _load_from_fitting(self, data: Any):
        """从拟合结果加载"""
        if isinstance(data, pd.DataFrame):
            self.processed_data = data
        else:
            self.processed_data = pd.DataFrame(data)
        self.name = "拟合结果"
    
    def get_processed_data(self) -> pd.DataFrame:
        """获取处理后的数据"""
        return self.processed_data
    
    def get_name(self) -> str:
        """获取数据名称"""
        return self.name


class DataManager(QObject):
    """
    数据管理器 - 支持两种接口
    
    管理所有数据对象
    """
    # 信号
    data_added = Signal(int)  # 参数：数据ID
    data_removed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_dict: Dict[int, Data] = {}
        self._counter: int = 0
    
    def add_data(self, name_or_item, dataframe_or_type=None) -> int:
        """
        添加新数据（支持两种接口）
        
        接口1（新版，推荐）：
            add_data(name: str, dataframe: Optional[pd.DataFrame] = None) -> int
            
        接口2（旧版，兼容）：
            add_data(item: Dict, itemtype: str) -> int
        
        返回:
            int: 数据ID
        """
        # 判断是新接口还是旧接口
        if isinstance(name_or_item, str):
            # 新接口：add_data(name, dataframe)
            name = name_or_item
            dataframe = dataframe_or_type
            
            # 创建简化的Data对象
            data = DataSimple(name, dataframe, parent=self)
            
        else:
            # 旧接口：add_data(item, itemtype)
            item = name_or_item
            itemtype = dataframe_or_type
            data = Data(item, itemtype, parent=self)
        
        # 分配ID并存储
        data_id = self._counter
        self._data_dict[data_id] = data
        self._counter += 1
        
        # 发射信号
        self.data_added.emit(data_id)
        
        return data_id
    
    def get_data(self, data_id: int) -> Optional[Data]:
        """获取指定ID的数据"""
        return self._data_dict.get(data_id)
    
    def remove_data(self, data_id: int) -> bool:
        """删除数据"""
        if data_id in self._data_dict:
            del self._data_dict[data_id]
            self.data_removed.emit(data_id)
            return True
        return False
    
    def get_all_data(self) -> Dict[int, Data]:
        """获取所有数据"""
        return self._data_dict.copy()

