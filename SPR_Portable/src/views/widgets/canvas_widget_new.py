# -*- coding: utf-8 -*-
"""
绘图画布组件 - 按照原项目方式重写

⭐ 关键改变：直接继承FigureCanvas，而不是QWidget包含FigureCanvas
"""
from PySide6.QtWidgets import QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import Signal
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


class CanvasWidgetDirect(FigureCanvas):
    """
    直接继承FigureCanvas的画布组件
    
    ⭐ 参考原项目的成功实现
    
    关键点：
    1. 直接继承FigureCanvas（不是QWidget）
    2. 在__init__中传入Figure
    3. 简化架构，减少层级
    """
    
    plot_updated = Signal()
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        """
        初始化Canvas
        
        参数：
            parent: 父窗口
            width: Figure宽度（英寸）
            height: Figure高度（英寸）
            dpi: 分辨率
        """
        # 1. 创建Figure
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        
        # 2. 创建Axes
        self.axes = self.fig.add_subplot(111)
        
        # 3. 调用父类初始化（传入Figure）
        super(CanvasWidgetDirect, self).__init__(self.fig)
        
        # 4. 设置父窗口
        if parent:
            self.setParent(parent)
        
        # 5. 尺寸策略与最小尺寸，确保在布局中有空间
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 150)

        # 6. 初始化样式
        self._init_plot_style()
        
        # 7. 设置默认轴标签
        self.axes.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
        self.axes.set_ylabel('Response (RU)', fontsize=12, fontweight='bold')
        self.axes.set_title('SPR Sensor Data', fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3, linestyle='--')
        
        # 8. 保存当前数据
        self._current_data = {}
        
        print(f"[CanvasWidgetDirect] 初始化完成")
    
    def _init_plot_style(self):
        """初始化绘图样式"""
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except:
            try:
                plt.style.use('seaborn-darkgrid')
            except:
                pass
        
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def plot_line(self, x_data, y_data, label='Data', color='#1a73e8', 
                  linewidth=2, marker='o', markersize=4, linestyle='-', **kwargs):
        """
        绘制折线图
        
        ⭐ 参考原项目：直接操作self.axes
        """
        print(f"[CanvasWidgetDirect] 开始绘制: {label}, 数据点数={len(x_data)}")
        
        # 1. 清空当前图形
        self.axes.clear()
        
        # 2. 绘制数据
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
        
        if marker == 'none':
            plot_kwargs.pop('marker')
            plot_kwargs.pop('markersize')
            plot_kwargs.pop('markerfacecolor')
            plot_kwargs.pop('markeredgecolor')
            plot_kwargs.pop('markeredgewidth')
        
        plot_kwargs.update(kwargs)
        
        self.axes.plot(x_data, y_data, **plot_kwargs)
        
        # 3. 设置样式
        self.axes.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
        self.axes.set_ylabel('Response (RU)', fontsize=12, fontweight='bold')
        self.axes.set_title('SPR Sensor Data', fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3, linestyle='--')
        self.axes.legend(loc='best', fontsize=10)
        
        # 4. 自动缩放
        self.axes.autoscale()
        
        # 5. 刷新（使用draw而不是draw_idle，参考原项目）
        try:
            self.fig.tight_layout()
        except Exception as e:
            print(f"[CanvasWidgetDirect] tight_layout警告: {e}")
        
        self.draw()  # ⭐ 原项目用的是draw()
        
        # 6. 保存数据
        self._current_data = {
            'type': 'line',
            'x': x_data,
            'y': y_data,
            'label': label
        }
        
        print(f"[CanvasWidgetDirect] ✅ 绘制完成")
        self.plot_updated.emit()
    
    def plot_fitting(self, x_data, y_data, y_pred, 
                     data_label='Experimental', 
                     fit_label='Fitted',
                     title='SPR Fitting Result'):
        """绘制拟合结果"""
        print(f"[CanvasWidgetDirect] 绘制拟合图")
        
        self.axes.clear()
        
        # 实验数据（散点）
        self.axes.scatter(x_data, y_data, 
                         label=data_label,
                         color='#1a73e8',
                         s=30,
                         alpha=0.6,
                         edgecolors='white',
                         linewidths=1)
        
        # 拟合曲线
        self.axes.plot(x_data, y_pred,
                      label=fit_label,
                      color='#ea4335',
                      linewidth=2,
                      linestyle='-')
        
        # 设置样式
        self.axes.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
        self.axes.set_ylabel('Response (RU)', fontsize=12, fontweight='bold')
        self.axes.set_title(title, fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3, linestyle='--')
        self.axes.legend(loc='best', fontsize=10)
        
        # 刷新
        try:
            self.fig.tight_layout()
        except:
            pass
        
        self.draw()
        
        self._current_data = {
            'type': 'fitting',
            'x': x_data,
            'y': y_data,
            'y_pred': y_pred
        }
        
        print(f"[CanvasWidgetDirect] ✅ 拟合图绘制完成")
        self.plot_updated.emit()
    
    def plot_multi_curves(self, data_dict, title='SPR Multi-Curve Analysis'):
        """绘制多条曲线（对比图）"""
        self.axes.clear()
        colors = ['#1a73e8', '#ea4335', '#34a853', '#fbbc04', '#ff6d00', '#ab47bc']
        for idx, (label, (x_data, y_data)) in enumerate(data_dict.items()):
            color = colors[idx % len(colors)]
            self.axes.plot(x_data, y_data,
                           label=label,
                           color=color,
                           linewidth=2,
                           marker='o',
                           markersize=3)
        self.axes.set_xlabel('Time (s)', fontsize=12, fontweight='bold')
        self.axes.set_ylabel('Response (RU)', fontsize=12, fontweight='bold')
        self.axes.set_title(title, fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3, linestyle='--')
        self.axes.legend(loc='best', fontsize=9)
        try:
            self.fig.tight_layout()
        except:
            pass
        self.draw()
        self.plot_updated.emit()

    def clear_plot(self):
        """清空图表"""
        self.axes.clear()
        self.axes.set_xlabel('X')
        self.axes.set_ylabel('Y')
        self.axes.set_title('SPR Sensor Data')
        self.axes.grid(True, alpha=0.3)
        self.draw()
        self._current_data = {}
        print("[CanvasWidgetDirect] 图表已清空")
    
    def set_title(self, title: str):
        """设置标题"""
        self.axes.set_title(title, fontsize=14, fontweight='bold')
        self.draw()
    
    def set_xlabel(self, label: str):
        """设置X轴标签"""
        self.axes.set_xlabel(label, fontsize=12, fontweight='bold')
        self.draw()
    
    def set_ylabel(self, label: str):
        """设置Y轴标签"""
        self.axes.set_ylabel(label, fontsize=12, fontweight='bold')
        self.draw()
    
    def set_grid(self, enable: bool = True):
        """启用/禁用网格"""
        self.axes.grid(enable, alpha=0.3, linestyle='--')
        self.draw()


class CanvasWidgetWithToolbar(QWidget):
    """
    带工具栏的Canvas组件
    
    用于在MainWindow中使用，包含：
    - CanvasWidgetDirect（直接继承FigureCanvas）
    - NavigationToolbar
    """
    
    plot_updated = Signal()
    
    def __init__(self, parent=None, dpi=100):
        super().__init__(parent)
        self._setup_ui(dpi)
    
    def _setup_ui(self, dpi):
        """设置UI"""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        # 创建直接继承FigureCanvas的Canvas
        self.canvas_widget = CanvasWidgetDirect(self, dpi=dpi)
        
        # 创建工具栏
        self.toolbar = NavigationToolbar(self.canvas_widget, self)
        
        # 添加到布局
        self._layout.addWidget(self.toolbar)
        self._layout.addWidget(self.canvas_widget)
        
        # 连接信号
        self.canvas_widget.plot_updated.connect(self.plot_updated.emit)
        
        print("[CanvasWidgetWithToolbar] 初始化完成")
    
    def _recreate_canvas(self, dpi=100):
        """重新创建Canvas，参考原项目每次绘图新建实例的做法"""
        try:
            # 从布局中移除旧的canvas
            self._layout.removeWidget(self.canvas_widget)
            self.canvas_widget.setParent(None)
            self.canvas_widget.deleteLater()
        except Exception:
            pass

        # 新建canvas并添加
        self.canvas_widget = CanvasWidgetDirect(self, dpi=dpi)
        self.toolbar.setParent(None)
        self.toolbar.deleteLater()
        self.toolbar = NavigationToolbar(self.canvas_widget, self)
        self._layout.insertWidget(0, self.toolbar)
        self._layout.addWidget(self.canvas_widget)

    # 代理/封装方法：在绘图前重新创建canvas
    def plot_line(self, *args, **kwargs):
        self._recreate_canvas(dpi=self.canvas_widget.fig.dpi)
        return self.canvas_widget.plot_line(*args, **kwargs)
    
    def plot_fitting(self, *args, **kwargs):
        self._recreate_canvas(dpi=self.canvas_widget.fig.dpi)
        return self.canvas_widget.plot_fitting(*args, **kwargs)

    def plot_multi_curves(self, *args, **kwargs):
        self._recreate_canvas(dpi=self.canvas_widget.fig.dpi)
        return self.canvas_widget.plot_multi_curves(*args, **kwargs)
    
    def clear_plot(self):
        return self.canvas_widget.clear_plot()
    
    def set_title(self, title: str):
        return self.canvas_widget.set_title(title)
    
    def set_xlabel(self, label: str):
        return self.canvas_widget.set_xlabel(label)
    
    def set_ylabel(self, label: str):
        return self.canvas_widget.set_ylabel(label)
    
    def set_grid(self, enable: bool = True):
        return self.canvas_widget.set_grid(enable)

