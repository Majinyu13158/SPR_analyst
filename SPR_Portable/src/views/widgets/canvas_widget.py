# -*- coding: utf-8 -*-
"""
绘图画布组件 - 从旧版本迁移

原始文件: spr_gui_main.py - CanvasWidget, CanvasWidget_figure
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QSizePolicy
from PySide6.QtCore import Signal, Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import numpy as np


class CustomNavigationToolbar(NavigationToolbar):
    """
    自定义导航工具栏
    
    功能：
        - 移除不需要的按钮
        - 自定义图标样式
    """
    
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)
        self._setup_toolbar()
    
    def _setup_toolbar(self):
        """自定义工具栏"""
        # 移除"子图配置"按钮
        actions = self.actions()
        for action in actions:
            if action.text() == 'Subplots':
                self.removeAction(action)
        
        # 应用样式
        self.setStyleSheet("""
            QToolBar {
                background: #f5f5f5;
                border-bottom: 1px solid #ddd;
                padding: 2px;
            }
            QToolButton {
                background: transparent;
                border: none;
                padding: 4px;
                margin: 2px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background: #e0e0e0;
            }
            QToolButton:pressed {
                background: #d0d0d0;
            }
        """)


class CanvasWidget(QWidget):
    """
    Matplotlib画布组件
    
    从旧版本迁移：CanvasWidget, CanvasWidget_figure
    
    功能：
        - Matplotlib集成
        - 工具栏（缩放、平移、保存）
        - 绘制折线图、散点图
        - 图例、标题、轴标签
    
    信号：
        plot_updated: 图表更新完成
    """
    
    plot_updated = Signal()
    
    def __init__(self, parent=None, dpi=100):
        super().__init__(parent)
        self.dpi = dpi
        self._setup_ui()
        self._init_plot_style()
        
        # 当前绘图数据（用于刷新）
        self._current_data = {}
        # 视图持久化与交互状态
        self._persist_xlim = None
        self._persist_ylim = None
        self._user_changed_view = False
        self._is_panning = False
        self._pan_start = None  # (xdata, ydata)
        self._pan_orig_xlim = None
        self._pan_orig_ylim = None
        # 连接交互事件
        self._connect_interactions()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建Figure和Canvas
        self.figure = Figure(figsize=(8, 6), dpi=self.dpi)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 创建工具栏
        self.toolbar = CustomNavigationToolbar(self.canvas, self)
        
        # 添加到布局
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # 创建默认子图
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_title('SPR Sensor Data')
        self.ax.grid(True, alpha=0.3)
    
    def _init_plot_style(self):
        """初始化绘图样式"""
        # 使用seaborn风格
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except:
            try:
                plt.style.use('seaborn-darkgrid')
            except:
                pass  # 如果没有seaborn样式，使用默认
        
        # 设置中文字体（如果需要）
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    # ========== 公共绘图接口 ==========
    def _connect_interactions(self):
        """连接鼠标滚轮缩放、右键拖拽平移、双击复位"""
        try:
            self.canvas.mpl_disconnect(getattr(self, '_cid_scroll', None) or 0)
            self.canvas.mpl_disconnect(getattr(self, '_cid_press', None) or 0)
            self.canvas.mpl_disconnect(getattr(self, '_cid_release', None) or 0)
            self.canvas.mpl_disconnect(getattr(self, '_cid_motion', None) or 0)
        except Exception:
            pass
        self._cid_scroll = self.canvas.mpl_connect('scroll_event', self._on_scroll)
        self._cid_press = self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self._cid_release = self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self._cid_motion = self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)

    def _apply_persisted_view(self):
        if self._persist_xlim is not None and self._persist_ylim is not None:
            try:
                self.ax.set_xlim(self._persist_xlim)
                self.ax.set_ylim(self._persist_ylim)
            except Exception:
                pass

    def _update_persisted_view(self):
        try:
            self._persist_xlim = tuple(self.ax.get_xlim())
            self._persist_ylim = tuple(self.ax.get_ylim())
        except Exception:
            pass

    def _data_bounds_from_xy(self, x, y):
        try:
            import numpy as _np
            xmin = float(_np.nanmin(x))
            xmax = float(_np.nanmax(x))
            ymin = float(_np.nanmin(y))
            ymax = float(_np.nanmax(y))
            if xmin == xmax:
                xmin -= 1.0; xmax += 1.0
            if ymin == ymax:
                ymin -= 1.0; ymax += 1.0
            return (xmin, xmax, ymin, ymax)
        except Exception:
            return None

    def _reset_view_to_data(self):
        b = self._current_data or {}
        if b.get('type') == 'line':
            bounds = self._data_bounds_from_xy(b.get('x'), b.get('y'))
        elif b.get('type') == 'fitting':
            bounds = self._data_bounds_from_xy(b.get('x'), b.get('y_pred'))
        elif b.get('type') == 'multi':
            # multi: 存的是列表
            all_x = []
            all_y = []
            for _, (xv, yv) in (b.get('series') or {}).items():
                all_x.extend(list(xv))
                all_y.extend(list(yv))
            bounds = self._data_bounds_from_xy(np.array(all_x), np.array(all_y))
        else:
            bounds = None
        if bounds:
            (xmin, xmax, ymin, ymax) = bounds
            self.ax.set_xlim(xmin, xmax)
            self.ax.set_ylim(ymin, ymax)
            self.canvas.draw_idle()
            self._user_changed_view = False
            self._update_persisted_view()

    def _on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        # 缩放中心：鼠标位置
        xdata, ydata = event.xdata, event.ydata
        cur_xlim = list(self.ax.get_xlim())
        cur_ylim = list(self.ax.get_ylim())
        scale = 1.2 if event.button == 'up' else (1/1.2)
        # X轴
        left = xdata - (xdata - cur_xlim[0]) * scale
        right = xdata + (cur_xlim[1] - xdata) * scale
        # Y轴
        bottom = ydata - (ydata - cur_ylim[0]) * scale
        top = ydata + (cur_ylim[1] - ydata) * scale
        try:
            self.ax.set_xlim(left, right)
            self.ax.set_ylim(bottom, top)
        except Exception:
            return
        self.canvas.draw_idle()
        self._user_changed_view = True
        self._update_persisted_view()

    def _on_mouse_press(self, event):
        # 右键拖拽平移；左键双击复位
        if event.inaxes != self.ax:
            return
        if getattr(event, 'dblclick', False) and event.button == 1:
            self._reset_view_to_data()
            return
        if event.button == 3:
            self._is_panning = True
            self._pan_start = (event.xdata, event.ydata)
            self._pan_orig_xlim = self.ax.get_xlim()
            self._pan_orig_ylim = self.ax.get_ylim()

    def _on_mouse_release(self, event):
        if event.button == 3:
            self._is_panning = False
            self._pan_start = None
            self._pan_orig_xlim = None
            self._pan_orig_ylim = None

    def _on_mouse_move(self, event):
        if not self._is_panning or event.inaxes != self.ax or self._pan_start is None:
            return
        x0, y0 = self._pan_start
        dx = event.xdata - x0 if event.xdata is not None else 0
        dy = event.ydata - y0 if event.ydata is not None else 0
        try:
            self.ax.set_xlim(self._pan_orig_xlim[0] - dx, self._pan_orig_xlim[1] - dx)
            self.ax.set_ylim(self._pan_orig_ylim[0] - dy, self._pan_orig_ylim[1] - dy)
        except Exception:
            return
        self.canvas.draw_idle()
        self._user_changed_view = True
        self._update_persisted_view()
    
    def plot_line(self, x_data, y_data, label='Data', color='#1a73e8', 
                  linewidth=2, marker='o', markersize=4, linestyle='-', **kwargs):
        """
        绘制折线图（⭐ 阶段1改进：支持更多样式参数）
        
        参数:
            x_data: X轴数据（数组）
            y_data: Y轴数据（数组）
            label: 图例标签
            color: 线条颜色
            linewidth: 线宽
            marker: 标记样式
            markersize: 标记大小
            linestyle: 线型 ('-', '--', '-.', ':', 'none')
            **kwargs: 其他matplotlib参数
        """
        self.ax.clear()  # 清除现有图形
        
        # ⭐ 绘制（支持更多样式参数）
        plot_kwargs = {
            'label': label,
            'color': color,
            'linewidth': linewidth,
            'linestyle': linestyle,
            'marker': marker,
            'markersize': markersize,
            'markerfacecolor': 'white',
            'markeredgecolor': color,
            'markeredgewidth': 1.5
        }
        
        # 如果marker为'none'，移除标记相关参数
        if marker == 'none':
            plot_kwargs.pop('marker')
            plot_kwargs.pop('markersize')
            plot_kwargs.pop('markerfacecolor')
            plot_kwargs.pop('markeredgecolor')
            plot_kwargs.pop('markeredgewidth')
        
        # 合并用户提供的额外参数
        plot_kwargs.update(kwargs)
        
        self.ax.plot(x_data, y_data, **plot_kwargs)
        
        # 设置样式
        self.ax.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Response (RU)', fontsize=12, fontweight='bold')
        self.ax.set_title('SPR Sensor Data', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.legend(loc='best', fontsize=10)
        
        # ⭐ 方案2：使用draw_idle()代替draw()
        try:
            self.figure.tight_layout()
        except Exception as e:
            print(f"[CanvasWidget] tight_layout警告: {e}")
        
        # 使用draw_idle()在事件循环空闲时重绘（更安全）
        if self._user_changed_view and self._persist_xlim and self._persist_ylim:
            self._apply_persisted_view()
        self.canvas.draw_idle()
        self.canvas.flush_events()  # 刷新事件队列
        
        # 保存数据
        self._current_data = {
            'type': 'line',
            'x': x_data,
            'y': y_data,
            'label': label
        }
        self._update_persisted_view()
        
        self.plot_updated.emit()
        print(f"[CanvasWidget] ✅ plot_line完成，使用draw_idle()")
    
    def plot_fitting(self, x_data, y_data, y_pred, 
                     data_label='Experimental', 
                     fit_label='Fitted',
                     title='SPR Fitting Result'):
        """
        绘制拟合结果（实验数据 + 拟合曲线）
        
        参数:
            x_data: X轴数据
            y_data: 实验Y数据
            y_pred: 拟合Y数据
            data_label: 实验数据标签
            fit_label: 拟合曲线标签
            title: 图表标题
        """
        self.ax.clear()
        
        # 绘制实验数据（散点）
        self.ax.scatter(x_data, y_data, 
                       label=data_label,
                       color='#1a73e8',
                       s=30,
                       alpha=0.6,
                       edgecolors='white',
                       linewidths=1)
        
        # 绘制拟合曲线
        self.ax.plot(x_data, y_pred,
                    label=fit_label,
                    color='#ea4335',
                    linewidth=2,
                    linestyle='-')
        
        # 设置样式
        self.ax.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Response (RU)', fontsize=12, fontweight='bold')
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.legend(loc='best', fontsize=10)
        
        # ⭐ 方案2：使用draw_idle()代替draw()
        try:
            self.figure.tight_layout()
        except Exception as e:
            print(f"[CanvasWidget] tight_layout警告: {e}")
        
        # 使用draw_idle()在事件循环空闲时重绘
        if self._user_changed_view and self._persist_xlim and self._persist_ylim:
            self._apply_persisted_view()
        self.canvas.draw_idle()
        self.canvas.flush_events()
        
        # 保存数据
        self._current_data = {
            'type': 'fitting',
            'x': x_data,
            'y': y_data,
            'y_pred': y_pred
        }
        self._update_persisted_view()
        
        print(f"[CanvasWidget] ✅ plot_fitting完成，使用draw_idle()")
        
        self.plot_updated.emit()
    
    def plot_multi_curves(self, data_dict, title='SPR Multi-Curve Analysis'):
        """
        绘制多条曲线
        
        参数:
            data_dict: 字典 {'label1': (x1, y1), 'label2': (x2, y2), ...}
            title: 图表标题
        """
        self.ax.clear()
        
        # 颜色列表
        colors = ['#1a73e8', '#ea4335', '#34a853', '#fbbc04', '#ff6d00', '#ab47bc']
        
        # 绘制每条曲线
        for idx, (label, (x_data, y_data)) in enumerate(data_dict.items()):
            color = colors[idx % len(colors)]
            self.ax.plot(x_data, y_data,
                        label=label,
                        color=color,
                        linewidth=2,
                        marker='o',
                        markersize=3)
        
        # 设置样式
        self.ax.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
        self.ax.set_ylabel('Response (RU)', fontsize=12, fontweight='bold')
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.legend(loc='best', fontsize=9)
        
        # ⭐ 方案2：使用draw_idle()代替draw()
        try:
            self.figure.tight_layout()
        except Exception as e:
            print(f"[CanvasWidget] tight_layout警告: {e}")
        if self._user_changed_view and self._persist_xlim and self._persist_ylim:
            self._apply_persisted_view()
        self.canvas.draw_idle()
        self.canvas.flush_events()
        
        # 保存数据以便复位
        self._current_data = {
            'type': 'multi',
            'series': data_dict
        }
        self._update_persisted_view()
        print(f"[CanvasWidget] ✅ plot_multi_curves完成，使用draw_idle()")
        self.plot_updated.emit()
    
    def clear_plot(self):
        """清空图表（⭐ 方案2：使用draw_idle）"""
        self.ax.clear()
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_title('SPR Sensor Data')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw_idle()
        self._current_data = {}
        print("[CanvasWidget] 图表已清空")
    
    def refresh(self):
        """刷新当前图表（⭐ 方案2：使用draw_idle）"""
        self.canvas.draw_idle()
        self.canvas.flush_events()
    
    def export_image(self, file_path, dpi=300):
        """
        导出图表为图片
        
        参数:
            file_path: 保存路径
            dpi: 分辨率
        """
        self.figure.savefig(file_path, dpi=dpi, bbox_inches='tight')
    
    # ========== 图表属性设置 ==========
    
    def set_title(self, title: str):
        """设置标题（⭐ 方案2：使用draw_idle）"""
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.canvas.draw_idle()
    
    def set_xlabel(self, label: str):
        """设置X轴标签（⭐ 方案2：使用draw_idle）"""
        self.ax.set_xlabel(label, fontsize=12, fontweight='bold')
        self.canvas.draw_idle()
    
    def set_ylabel(self, label: str):
        """设置Y轴标签（⭐ 方案2：使用draw_idle）"""
        self.ax.set_ylabel(label, fontsize=12, fontweight='bold')
        self.canvas.draw_idle()
    
    def set_xlim(self, xmin, xmax):
        """设置X轴范围（⭐ 方案2：使用draw_idle）"""
        self.ax.set_xlim(xmin, xmax)
        self.canvas.draw_idle()
    
    def set_ylim(self, ymin, ymax):
        """设置Y轴范围（⭐ 方案2：使用draw_idle）"""
        self.ax.set_ylim(ymin, ymax)
        self.canvas.draw_idle()
    
    def enable_grid(self, enable: bool = True):
        """启用/禁用网格（⭐ 方案2：使用draw_idle）"""
        self.ax.grid(enable, alpha=0.3, linestyle='--')
        self.canvas.draw_idle()

