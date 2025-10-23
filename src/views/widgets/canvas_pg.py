# -*- coding: utf-8 -*-
"""
PgCanvasWidget - 基于 PySide6 + pyqtgraph 的高性能绘图适配器

对外 API 与现有 CanvasWidget 保持一致：
- plot_line(x, y, label, ...)
- plot_fitting(x, y, y_pred, ...)
- plot_multi_curves(data_dict)
- clear_plot(), set_title(), set_xlabel(), set_ylabel(), set_grid()

优势：
- 原生支持滚轮缩放/拖拽平移/框选缩放
- 下采样与视图裁剪，交互更流畅
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMenu
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction, QCursor

import os
os.environ.setdefault('PYQTGRAPH_QT_LIB', 'PySide6')

import numpy as np
import pyqtgraph as pg


class PgCanvasWidget(QWidget):
    plot_updated = Signal()
    edit_style_requested = Signal()  # 请求编辑样式
    export_figure_requested = Signal()  # 请求导出图表

    def __init__(self, parent=None, dpi: int = 100):
        super().__init__(parent)
        self._init_ui()
        self._init_pg()
        self._current_state = None  # 持久化视图
        self._series_items = []     # 当前绘制的曲线项
        self._setup_context_menu()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

    def _init_pg(self):
        # 全局配置
        pg.setConfigOptions(antialias=False, useOpenGL=False, background='w', foreground='k')
        vb = self.plot_widget.getViewBox()
        # 背景/前景与坐标轴样式
        try:
            self.plot_widget.setBackground('w')
        except Exception:
            pass
        try:
            for ax in ('left', 'bottom', 'right', 'top'):
                a = self.plot_widget.getPlotItem().getAxis(ax)
                if a is not None:
                    a.setPen('k')
                    a.setTextPen('k')
        except Exception:
            pass
        # 网格
        self.plot_widget.showGrid(x=True, y=True, alpha=0.12)
        # 图例
        try:
            self.plot_widget.addLegend(offset=(10, 10))
        except Exception:
            pass
        # 交互：滚轮缩放/拖拽平移 默认支持；双击复位
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)
        self.set_title('SPR Sensor Data')
        self.set_xlabel('Time (s)')
        self.set_ylabel('Response (RU)')

    # ========== 内部辅助 ==========
    def _clear_items(self):
        for it in self._series_items:
            try:
                self.plot_widget.removeItem(it)
            except Exception:
                pass
        self._series_items = []

    def _persist_view(self):
        try:
            vb = self.plot_widget.getViewBox()
            self._current_state = vb.viewRange()  # [[xmin,xmax],[ymin,ymax]]
        except Exception:
            self._current_state = None

    def _restore_view(self):
        if not self._current_state:
            return
        try:
            (xr, yr) = self._current_state
            self.plot_widget.getViewBox().setRange(xRange=xr, yRange=yr, padding=0.0)
        except Exception:
            pass

    def _setup_context_menu(self):
        """设置右键菜单"""
        self.plot_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.plot_widget.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        
        # 编辑样式
        style_action = QAction("🎨 编辑样式", self)
        style_action.triggered.connect(self.edit_style_requested.emit)
        menu.addAction(style_action)
        
        menu.addSeparator()
        
        # 导出图表
        export_action = QAction("📊 导出图表", self)
        export_action.triggered.connect(self.export_figure_requested.emit)
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        # 重置视图
        reset_action = QAction("🔄 重置视图", self)
        reset_action.triggered.connect(lambda: self.plot_widget.enableAutoRange())
        menu.addAction(reset_action)
        
        # 显示菜单
        menu.exec(self.plot_widget.mapToGlobal(pos))
    
    def _on_mouse_click(self, ev):
        # 左键双击复位
        if ev is None:
            return
        if ev.double():
            try:
                self.plot_widget.enableAutoRange()
            except Exception:
                pass

    # ========== 外部 API ==========
    def plot_line(self, x_data, y_data, label='Data', color='#1a73e8',
                  linewidth=2, marker='o', markersize=3, linestyle='-'):
        self._clear_items()
        self.plot_widget.clear()
        pen = pg.mkPen(color=color, width=linewidth)
        symbol = None if marker == 'none' else 'o'
        xv = np.asarray(x_data, dtype=float)
        yv = np.asarray(y_data, dtype=float)
        mask = np.isfinite(xv) & np.isfinite(yv)
        item = self.plot_widget.plot(xv[mask], yv[mask],
                                     pen=pen,
                                     symbol=symbol,
                                     symbolBrush='w',
                                     symbolPen=pen,
                                     symbolSize=markersize,
                                     name=label)
        try:
            item.setClipToView(True)
            # 下采样
            if hasattr(item, 'setDownsampling'):
                item.setDownsampling(auto=True, method='peak')
        except Exception:
            pass
        self._series_items.append(item)
        self._persist_view()
        self.plot_updated.emit()

    def plot_fitting(self, x_data, y_data, y_pred,
                     data_label='Experimental',
                     fit_label='Fitted',
                     title='SPR Fitting Result'):
        self._clear_items()
        self.plot_widget.clear()
        # 实验数据（散点）
        exp_pen = pg.mkPen(color='#1a73e8', width=1)
        xv = np.asarray(x_data, dtype=float)
        yv = np.asarray(y_data, dtype=float)
        mask = np.isfinite(xv) & np.isfinite(yv)
        exp_item = self.plot_widget.plot(xv[mask], yv[mask],
                                         pen=None, symbol='o', symbolSize=4,
                                         symbolBrush='#1a73e8', symbolPen='w', name=data_label)
        # 拟合（线）
        fit_pen = pg.mkPen(color='#ea4335', width=2)
        yp = np.asarray(y_pred, dtype=float)
        mask2 = np.isfinite(xv) & np.isfinite(yp)
        fit_item = self.plot_widget.plot(xv[mask2], yp[mask2], pen=fit_pen, name=fit_label)
        for it in (exp_item, fit_item):
            it.setClipToView(True)
            try:
                if hasattr(it, 'setDownsampling'):
                    it.setDownsampling(auto=True, method='peak')
            except Exception:
                pass
            self._series_items.append(it)
        self.set_title(title)
        self._persist_view()
        self.plot_updated.emit()

    def plot_multi_curves(self, data_dict, title='SPR Multi-Curve Analysis'):
        self._clear_items()
        self.plot_widget.clear()
        colors = ['#1a73e8', '#ea4335', '#34a853', '#fbbc04', '#ff6d00', '#ab47bc', '#46bdc6', '#7a3cff']
        for idx, (label, (x, y)) in enumerate(data_dict.items()):
            pen = pg.mkPen(color=colors[idx % len(colors)], width=2)
            xv = np.asarray(x, dtype=float)
            yv = np.asarray(y, dtype=float)
            mask = np.isfinite(xv) & np.isfinite(yv)
            item = self.plot_widget.plot(xv[mask], yv[mask], pen=pen, name=str(label))
            try:
                item.setClipToView(True)
                if hasattr(item, 'setDownsampling'):
                    item.setDownsampling(auto=True, method='peak')
            except Exception:
                pass
            self._series_items.append(item)
        self.set_title(title)
        self._persist_view()
        self.plot_updated.emit()

    def clear_plot(self):
        self._clear_items()
        self.plot_widget.clear()
        self.plot_updated.emit()

    # ========== 属性设置 ==========
    def set_title(self, title: str):
        try:
            self.plot_widget.setTitle(title)
        except Exception:
            pass

    def set_xlabel(self, label: str):
        try:
            self.plot_widget.setLabel('bottom', label)
        except Exception:
            pass

    def set_ylabel(self, label: str):
        try:
            self.plot_widget.setLabel('left', label)
        except Exception:
            pass

    def set_grid(self, enable: bool = True):
        try:
            self.plot_widget.showGrid(x=enable, y=enable, alpha=0.15)
        except Exception:
            pass
    
    # ========== 图表导出 ==========
    def export_image(self, file_path: str, width: int = 1920, height: int = 1080):
        """
        导出图表为图片
        
        参数:
            file_path: 保存路径（支持 .png, .jpg, .svg, .pdf等）
            width: 图片宽度（像素）
            height: 图片高度（像素）
        
        说明:
            - PNG: 支持，推荐用于高质量输出
            - JPG: 支持，文件更小但有损
            - SVG: 支持，矢量格式（pyqtgraph内置）
            - PDF: 需要安装额外库（可选）
        """
        from pathlib import Path
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.svg':
                # SVG矢量格式导出
                from pyqtgraph.exporters import SVGExporter
                exporter = SVGExporter(self.plot_widget.plotItem)
                exporter.export(file_path)
            
            elif file_ext == '.pdf':
                # PDF导出（需要PyQt的QPrinter或通过matplotlib转换）
                # 方案1：先导出SVG再转PDF（需要额外库）
                # 方案2：使用ImageExporter导出高分辨率PNG
                from pyqtgraph.exporters import ImageExporter
                exporter = ImageExporter(self.plot_widget.plotItem)
                exporter.parameters()['width'] = width
                exporter.parameters()['height'] = height
                # 导出为临时PNG，然后转为PDF
                temp_png = str(Path(file_path).with_suffix('.png'))
                exporter.export(temp_png)
                
                # 使用PIL转换为PDF
                try:
                    from PIL import Image
                    img = Image.open(temp_png)
                    img.save(file_path, 'PDF', resolution=300.0)
                    Path(temp_png).unlink()  # 删除临时文件
                except ImportError:
                    # 如果没有PIL，就保留PNG格式
                    import shutil
                    shutil.move(temp_png, file_path)
                    print(f"⚠️ 未安装Pillow，PDF导出为PNG格式: {file_path}")
            
            else:
                # PNG/JPG等位图格式
                from pyqtgraph.exporters import ImageExporter
                exporter = ImageExporter(self.plot_widget.plotItem)
                exporter.parameters()['width'] = width
                exporter.parameters()['height'] = height
                exporter.export(file_path)
            
            print(f"✅ 图表已导出: {file_path}")
            return True, None
            
        except Exception as e:
            error_msg = f"导出图表时发生错误:\n{str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg


