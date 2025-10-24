# -*- coding: utf-8 -*-
"""
图表模型 - Prism风格架构

⭐ 阶段1改进：彻底分离数据和图表
- Figure只存储"如何绘图"，不存储"绘什么"
- 数据通过data_sources动态获取
- 支持多数据源对比图
"""
from PySide6.QtCore import QObject, Signal
from typing import Optional, List, Dict, Any
import numpy as np


class Figure(QObject):
    """
    图表类 - Prism风格
    
    核心原则：只存储数据源链接和绘图配置，不存储数据副本
    
    信号：
        figure_updated: 图表更新
        data_sources_changed: 数据源列表改变
    """
    
    figure_updated = Signal()
    data_sources_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 基本信息
        self.id: int = 0
        self.name: str = ""
        self.figure_type: str = "line"  # line, scatter, bar, fitting
        
        # ⭐ 数据源（支持多数据源）
        self.data_sources: List[int] = []  # 数据ID列表
        
        # ⭐ 绘图配置
        self.plot_config: Dict[str, Any] = {
            'title': 'SPR Sensor Data',
            'xlabel': 'Time (s)',
            'ylabel': 'Response (RU)',
            'grid': True,
            'legend_position': 'best'
        }
        
        # ⭐ 各数据源的样式配置
        self.styles: Dict[int, Dict[str, Any]] = {}
        # 格式：{data_id: {'color': '...', 'linewidth': 2, 'label': '...', ...}}
        
        # 兼容性：保留旧的属性名（用于SessionManager序列化）
        self.data_id: Optional[int] = None
        self.result_id: Optional[int] = None
    
    # ============================================================
    # ⭐ 新API：数据源管理
    # ============================================================
    
    def add_data_source(self, data_id: int, style: Dict[str, Any] = None):
        """
        添加数据源
        
        参数：
            data_id: 数据ID
            style: 样式配置，如 {'color': '#1a73e8', 'linewidth': 2, 'label': 'Data 1'}
        """
        if data_id not in self.data_sources:
            self.data_sources.append(data_id)
            self.styles[data_id] = style or self._default_style()
            
            # 兼容性：如果是第一个数据源，设置data_id
            if len(self.data_sources) == 1:
                self.data_id = data_id
            
            self.data_sources_changed.emit()
            self.figure_updated.emit()
            print(f"[Figure] {self.name} 添加数据源: {data_id}")
    
    def remove_data_source(self, data_id: int):
        """移除数据源"""
        if data_id in self.data_sources:
            self.data_sources.remove(data_id)
            if data_id in self.styles:
                del self.styles[data_id]
            
            # 兼容性：如果移除的是data_id，更新为第一个数据源或None
            if self.data_id == data_id:
                self.data_id = self.data_sources[0] if self.data_sources else None
            
            self.data_sources_changed.emit()
            self.figure_updated.emit()
            print(f"[Figure] {self.name} 移除数据源: {data_id}")
    
    def get_data_sources(self) -> List[int]:
        """获取所有数据源ID"""
        return self.data_sources.copy()
    
    def set_data_style(self, data_id: int, style: Dict[str, Any]):
        """设置数据源的样式"""
        if data_id in self.styles:
            self.styles[data_id].update(style)
            self.figure_updated.emit()
    
    def get_plot_data(self, data_manager):
        """
        ⭐ 核心方法：动态获取绘图数据
        
        这个方法在绘图时调用，从DataManager获取实时数据
        
        参数：
            data_manager: DataManager实例
        
        返回：
            List[Dict]: 绘图数据列表
            [
                {
                    'x': np.array([...]),
                    'y': np.array([...]),
                    'style': {'color': '...', 'linewidth': 2, ...},
                    'label': 'Data 1'
                },
                ...
            ]
        """
        plot_data = []
        
        for data_id in self.data_sources:
            data = data_manager.get_data(data_id)
            if data is None:
                print(f"[Figure] 警告：数据源{data_id}不存在")
                continue
            
            if data.dataframe is None or data.dataframe.empty:
                print(f"[Figure] 警告：数据源{data_id}为空")
                continue
            
            try:
                # ⭐ 优化：对于已知格式的数据，明确指定列名
                # 检查DataFrame列名，判断数据类型
                if hasattr(data, 'dataframe') and data.dataframe is not None:
                    df = data.dataframe
                    cols = list(df.columns)
                    # 宽表：Time + 多个浓度列 → 拆成多条曲线
                    if 'Time' in cols and len(cols) >= 2 and not ({'XValue','YValue'} <= set(cols)):
                        time_vals = df['Time'].to_numpy()
                        for conc_col in cols[1:]:
                            y_vals = df[conc_col].to_numpy()
                            style = self._default_style()
                            label = f"{data.name} - {conc_col}"
                            plot_data.append({
                                'x': time_vals,
                                'y': y_vals,
                                'style': style,
                                'label': label,
                                'data_id': data_id,
                                'data_name': data.name
                            })
                        # 已处理为多曲线，继续下一个数据源
                        continue
                    # 拟合曲线格式：XValue, YValue
                    if 'XValue' in cols and 'YValue' in cols:
                        x, y = data.get_xy_data(x_col='XValue', y_col='YValue', auto_sort=False)
                        print(f"[Figure] 拟合曲线数据: data_id={data_id}, X={x[:3]}..., Y={y[:3]}...")
                    # SPR实验数据格式：Time, Response/RU
                    elif 'Time' in cols:
                        y_col = 'Response' if 'Response' in cols else ('RU' if 'RU' in cols else None)
                        if y_col:
                            x, y = data.get_xy_data(x_col='Time', y_col=y_col, auto_sort=False)
                            print(f"[Figure] SPR数据: data_id={data_id}, X=Time, Y={y_col}")
                        else:
                            x, y = data.get_xy_data(auto_sort=False)
                            print(f"[Figure] SPR数据(智能): data_id={data_id}")
                    # 其他格式：使用智能选择
                    else:
                        x, y = data.get_xy_data(auto_sort=False)
                        print(f"[Figure] 智能选择: data_id={data_id}, 列={cols}")
                else:
                    x, y = data.get_xy_data(auto_sort=False)
                    print(f"[Figure] 默认提取: data_id={data_id}")
                
                # 验证数据（调试）
                if len(x) > 0 and len(y) > 0:
                    is_straight_line = all(abs(y[i] - x[i]) < 1e-10 for i in range(min(len(x), len(y))))
                    if is_straight_line:
                        print(f"[Figure] ⚠️ 警告：Y=X（直线）！data_id={data_id}, name={data.name}")
                
                style = self.styles.get(data_id, self._default_style())
                
                plot_data.append({
                    'x': x,
                    'y': y,
                    'style': style.copy(),
                    'label': style.get('label', data.name),
                    'data_id': data_id,
                    'data_name': data.name
                })
            except Exception as e:
                print(f"[Figure] 获取数据失败 data_id={data_id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return plot_data
    
    def _default_style(self) -> Dict[str, Any]:
        """生成默认样式"""
        colors = ['#1a73e8', '#ea4335', '#34a853', '#fbbc04', '#ff6d00', '#46bdc6']
        idx = len(self.styles) % len(colors)
        
        return {
            'color': colors[idx],
            'linewidth': 2.0,
            'marker': 'o',
            'markersize': 4.0,
            'linestyle': '-',
            'alpha': 1.0,
            'label': f'Data {len(self.styles) + 1}'
        }
    
    # ============================================================
    # 绘图配置方法
    # ============================================================
    
    def set_title(self, title: str):
        """设置标题"""
        self.plot_config['title'] = title
        self.figure_updated.emit()
    
    def set_labels(self, xlabel: str, ylabel: str):
        """设置轴标签"""
        self.plot_config['xlabel'] = xlabel
        self.plot_config['ylabel'] = ylabel
        self.figure_updated.emit()
    
    def set_grid(self, enabled: bool):
        """设置网格"""
        self.plot_config['grid'] = enabled
        self.figure_updated.emit()
    
    # ============================================================
    # 兼容性方法（保留旧API）
    # ============================================================
    
    def set_data_source(self, data_id: int):
        """
        设置数据源（兼容旧API）
        
        参数：
            data_id: 关联的数据ID
        """
        # 清空现有数据源，添加新的
        self.data_sources.clear()
        self.styles.clear()
        self.add_data_source(data_id)
    
    def get_data_source(self) -> Optional[int]:
        """
        获取关联的数据ID（兼容旧API）
        
        返回：
            Optional[int]: 第一个数据源ID，如果没有则返回None
        """
        return self.data_sources[0] if self.data_sources else None
    
    def set_result_source(self, result_id: int):
        """
        设置结果源（用于拟合曲线）
        
        参数：
            result_id: 关联的结果ID
        """
        self.result_id = result_id
        self.figure_updated.emit()
    
    def to_dict(self) -> dict:
        """转换为字典（用于序列化）"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.figure_type,
            'plot_config': self.plot_config.copy(),
            'data_sources': self.data_sources.copy(),
            'styles': {k: v.copy() for k, v in self.styles.items()},
            # 兼容性字段
            'data_id': self.data_id,
            'result_id': self.result_id
        }
    
    @classmethod
    def from_dict(cls, data: dict, parent=None) -> 'Figure':
        """从字典创建Figure对象"""
        figure = cls(parent)
        figure.id = data.get('id', 0)
        figure.name = data.get('name', '')
        figure.figure_type = data.get('type', 'line')
        figure.plot_config = data.get('plot_config', {})
        figure.data_sources = data.get('data_sources', [])
        figure.styles = data.get('styles', {})
        figure.data_id = data.get('data_id')
        figure.result_id = data.get('result_id')
        
        # 向后兼容：如果只有data_id没有data_sources，转换
        if not figure.data_sources and figure.data_id is not None:
            figure.data_sources = [figure.data_id]
            figure.styles[figure.data_id] = figure._default_style()
        
        return figure


class FigureManager(QObject):
    """
    图表管理器
    
    管理所有图表
    
    信号：
        figure_added: 图表添加 (figure_id)
        figure_removed: 图表删除 (figure_id)
        figure_updated: 图表更新 (figure_id)
    """
    
    figure_added = Signal(int)
    figure_removed = Signal(int)
    figure_updated = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._figures = {}  # {id: Figure}
        self._next_id = 1
    
    def add_figure(self, name: str, figure_type: str = "line") -> int:
        """
        添加图表
        
        返回:
            figure_id
        """
        figure = Figure(self)
        figure.id = self._next_id
        figure.name = name
        figure.figure_type = figure_type
        
        self._figures[self._next_id] = figure
        
        # 连接信号
        figure.figure_updated.connect(
            lambda: self.figure_updated.emit(figure.id)
        )
        
        self.figure_added.emit(self._next_id)
        
        self._next_id += 1
        return figure.id
    
    def get_figure(self, figure_id: int) -> Optional[Figure]:
        """获取图表"""
        return self._figures.get(figure_id)
    
    def remove_figure(self, figure_id: int):
        """删除图表"""
        if figure_id in self._figures:
            del self._figures[figure_id]
            self.figure_removed.emit(figure_id)
    
    def get_all_figures(self) -> list:
        """获取所有图表"""
        return list(self._figures.values())
    
    def clear(self):
        """清空所有图表"""
        self._figures.clear()
        self._next_id = 1

