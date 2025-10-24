"""
数据对比对话框

功能：
1. 同时显示多个数据及其拟合结果
2. 叠加绘图，自动颜色区分
3. 参数对比表格
4. 导出对比结果
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QListWidget, QTableWidget, QTableWidgetItem,
    QGroupBox, QCheckBox, QLabel, QMessageBox, QFileDialog,
    QListWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor
import pyqtgraph as pg
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime


class ComparisonDialog(QDialog):
    """数据对比对话框"""
    
    # 信号：请求添加数据
    add_data_requested = Signal()
    
    def __init__(self, data_manager, result_manager, figure_manager, link_manager, parent=None):
        super().__init__(parent)
        
        self.data_manager = data_manager
        self.result_manager = result_manager
        self.figure_manager = figure_manager
        self.link_manager = link_manager
        
        # 存储已选数据ID列表
        self.selected_data_ids: List[int] = []
        
        # 颜色映射
        self.color_map: Dict[int, QColor] = {}
        
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("数据对比")
        self.resize(1200, 800)
        
        layout = QVBoxLayout(self)
        
        # ========== 顶部工具栏 ==========
        toolbar = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ 添加数据")
        self.add_btn.setToolTip("添加数据到对比列表")
        self.add_btn.clicked.connect(self.add_data_requested.emit)
        toolbar.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("➖ 移除选中")
        self.remove_btn.setToolTip("从对比列表移除选中数据")
        self.remove_btn.clicked.connect(self._on_remove_selected)
        toolbar.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("🗑 清空全部")
        self.clear_btn.setToolTip("清空所有对比数据")
        self.clear_btn.clicked.connect(self._on_clear_all)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        
        self.export_chart_btn = QPushButton("📊 导出图表")
        self.export_chart_btn.clicked.connect(self._on_export_chart)
        toolbar.addWidget(self.export_chart_btn)
        
        self.export_table_btn = QPushButton("📋 导出表格")
        self.export_table_btn.clicked.connect(self._on_export_table)
        toolbar.addWidget(self.export_table_btn)
        
        layout.addLayout(toolbar)
        
        # ========== 主分割器 ==========
        main_splitter = QSplitter(Qt.Horizontal)
        
        # --- 左侧：数据列表与选项 ---
        left_panel = QGroupBox("对比数据")
        left_layout = QVBoxLayout(left_panel)
        
        # 数据列表
        self.data_list = QListWidget()
        self.data_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.data_list.itemChanged.connect(self._on_data_item_changed)
        left_layout.addWidget(self.data_list)
        
        # 显示选项（简化版）
        options_group = QGroupBox("显示选项")
        options_layout = QVBoxLayout(options_group)
        
        self.show_legend_check = QCheckBox("显示图例")
        self.show_legend_check.setChecked(True)
        self.show_legend_check.stateChanged.connect(self._on_option_changed)
        options_layout.addWidget(self.show_legend_check)
        
        self.normalize_check = QCheckBox("归一化显示")
        self.normalize_check.setChecked(False)
        self.normalize_check.stateChanged.connect(self._on_option_changed)
        options_layout.addWidget(self.normalize_check)
        
        left_layout.addWidget(options_group)
        
        # 统计信息
        self.stats_label = QLabel("当前对比: 0 个数据")
        self.stats_label.setStyleSheet("color: #666; padding: 5px;")
        left_layout.addWidget(self.stats_label)
        
        main_splitter.addWidget(left_panel)
        
        # --- 右侧：图表与参数表 ---
        right_panel = QSplitter(Qt.Vertical)
        
        # 图表区域
        chart_group = QGroupBox("叠加图表")
        chart_layout = QVBoxLayout(chart_group)
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', '响应值')
        self.plot_widget.setLabel('bottom', '浓度')
        self.plot_widget.addLegend()
        
        chart_layout.addWidget(self.plot_widget)
        right_panel.addWidget(chart_group)
        
        # 参数对比表
        table_group = QGroupBox("参数对比")
        table_layout = QVBoxLayout(table_group)
        
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(7)
        self.param_table.setHorizontalHeaderLabels([
            "数据名称", "拟合方法", "Kd", "Bmax", "R²", "RMSE", "拟合时间"
        ])
        self.param_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.param_table.setAlternatingRowColors(True)
        self.param_table.setSortingEnabled(True)
        
        table_layout.addWidget(self.param_table)
        right_panel.addWidget(table_group)
        
        # 设置右侧分割比例
        right_panel.setStretchFactor(0, 2)  # 图表占2/3
        right_panel.setStretchFactor(1, 1)  # 表格占1/3
        
        main_splitter.addWidget(right_panel)
        
        # 设置左右分割比例
        main_splitter.setStretchFactor(0, 1)  # 左侧占1/4
        main_splitter.setStretchFactor(1, 3)  # 右侧占3/4
        
        layout.addWidget(main_splitter)
        
        # ========== 底部按钮 ==========
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def add_data(self, data_id: int):
        """添加数据到对比列表"""
        if data_id in self.selected_data_ids:
            return  # 已存在
        
        data = self.data_manager.get_data(data_id)
        if data is None:
            return
        
        self.selected_data_ids.append(data_id)
        
        # 分配颜色
        self.color_map[data_id] = self._get_next_color()
        
        # 添加到列表
        item = QListWidgetItem(f"[{data_id}] {data.name}")
        item.setData(Qt.UserRole, data_id)
        item.setCheckState(Qt.Checked)
        item.setForeground(self.color_map[data_id])
        self.data_list.addItem(item)
        
        # 更新显示
        self._update_comparison()
    
    def _get_next_color(self) -> QColor:
        """获取下一个颜色（使用HSV色轮）"""
        n = len(self.selected_data_ids)
        hue = int(360 * n / max(10, n + 5))  # 分散色相
        saturation = 180 + (n % 3) * 25  # 在180-230之间变化
        value = 200 + (n % 2) * 30  # 在200-230之间变化
        return QColor.fromHsv(hue, saturation, value)
    
    @Slot()
    def _on_remove_selected(self):
        """移除选中的数据"""
        selected_items = self.data_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            data_id = item.data(Qt.UserRole)
            if data_id in self.selected_data_ids:
                self.selected_data_ids.remove(data_id)
            if data_id in self.color_map:
                del self.color_map[data_id]
            self.data_list.takeItem(self.data_list.row(item))
        
        self._update_comparison()
    
    @Slot()
    def _on_clear_all(self):
        """清空所有数据"""
        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有对比数据吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.selected_data_ids.clear()
            self.color_map.clear()
            self.data_list.clear()
            self._update_comparison()
    
    @Slot()
    def _on_data_item_changed(self, item: QListWidgetItem):
        """数据项勾选状态改变"""
        self._update_comparison()
    
    @Slot()
    def _on_option_changed(self):
        """显示选项改变"""
        self._update_comparison()
    
    def _update_comparison(self):
        """更新对比显示"""
        self._update_chart()
        self._update_param_table()
        self._update_stats()
    
    def _update_chart(self):
        """更新对比图表"""
        # ⭐ 清除旧图表
        self.plot_widget.clear()
        
        if not self.selected_data_ids:
            return
        
        # 获取选项
        show_legend = self.show_legend_check.isChecked()
        normalize = self.normalize_check.isChecked()
        
        # 重新添加图例（如果需要）
        if show_legend:
            self.plot_widget.addLegend()
        
        # ⭐ 遍历每个数据项，绘制所有已勾选的数据
        for i in range(self.data_list.count()):
            item = self.data_list.item(i)
            if item.checkState() != Qt.Checked:
                continue
            
            data_id = item.data(Qt.UserRole)
            data = self.data_manager.get_data(data_id)
            if data is None:
                continue
            
            color = self.color_map[data_id]
            color_tuple = (color.red(), color.green(), color.blue())
            
            # 获取数据
            df = data.dataframe
            if df is None or df.empty:
                continue
            
            x_data = df.iloc[:, 0].values
            y_data = df.iloc[:, 1].values
            
            # 归一化处理
            if normalize:
                y_data = self._normalize_data(y_data)
            
            # ⭐ 绘制原始数据（连线图 + 小圆点）
            self.plot_widget.plot(
                x_data, y_data,
                pen=pg.mkPen(color_tuple, width=2),  # 连线
                symbol='o',
                symbolSize=5,
                symbolBrush=color_tuple,
                symbolPen=None,
                name=f"{data.name}"
            )
    
    def _normalize_data(self, y_data: np.ndarray) -> np.ndarray:
        """归一化数据到0-1"""
        y_min, y_max = np.nanmin(y_data), np.nanmax(y_data)
        if y_max > y_min:
            return (y_data - y_min) / (y_max - y_min)
        return y_data
    
    def _update_param_table(self):
        """更新参数对比表"""
        self.param_table.setRowCount(0)
        
        if not self.selected_data_ids:
            return
        
        # 遍历每个数据，查找其拟合结果
        for i in range(self.data_list.count()):
            item = self.data_list.item(i)
            if item.checkState() != Qt.Checked:
                continue
            
            data_id = item.data(Qt.UserRole)
            data = self.data_manager.get_data(data_id)
            if data is None:
                continue
            
            # 查找结果
            result = self._get_result_for_data(data_id)
            if result is None:
                continue
            
            # 添加行
            row = self.param_table.rowCount()
            self.param_table.insertRow(row)
            
            # 填充数据
            self.param_table.setItem(row, 0, QTableWidgetItem(data.name))
            
            # 提取参数
            params = result.get_parameters()
            method = params.get('Method', ('未知', None, ''))[0] if 'Method' in params else '未知'
            kd = params.get('Kd', (None, None, ''))[0] if 'Kd' in params else None
            bmax = params.get('Bmax', (None, None, ''))[0] if 'Bmax' in params else None
            
            self.param_table.setItem(row, 1, QTableWidgetItem(str(method)))
            self.param_table.setItem(row, 2, QTableWidgetItem(f"{kd:.4f}" if kd is not None else "N/A"))
            self.param_table.setItem(row, 3, QTableWidgetItem(f"{bmax:.4f}" if bmax is not None else "N/A"))
            
            # R² 和 RMSE
            r2 = result.r2
            rmse = result.rmse
            self.param_table.setItem(row, 4, QTableWidgetItem(f"{r2:.4f}" if r2 is not None else "N/A"))
            self.param_table.setItem(row, 5, QTableWidgetItem(f"{rmse:.4f}" if rmse is not None else "N/A"))
            
            # 时间戳
            timestamp = result.timestamp if hasattr(result, 'timestamp') else "未知"
            self.param_table.setItem(row, 6, QTableWidgetItem(str(timestamp)))
            
            # 高亮最佳拟合（最高R²）
            if r2 is not None and r2 >= 0.95:
                for col in range(7):
                    item = self.param_table.item(row, col)
                    if item:
                        item.setBackground(QColor(200, 255, 200))  # 浅绿色
    
    def _get_result_for_data(self, data_id: int):
        """获取数据对应的拟合结果"""
        # 遍历所有结果，找到data_source匹配的
        for result in self.result_manager.get_all_results():
            if hasattr(result, 'data_source') and result.data_source == data_id:
                return result
        return None
    
    def _update_stats(self):
        """更新统计信息"""
        checked_count = sum(
            1 for i in range(self.data_list.count())
            if self.data_list.item(i).checkState() == Qt.Checked
        )
        total_count = len(self.selected_data_ids)
        self.stats_label.setText(f"当前对比: {checked_count}/{total_count} 个数据")
    
    @Slot()
    def _on_export_chart(self):
        """导出对比图表"""
        if not self.selected_data_ids:
            QMessageBox.warning(self, "无数据", "没有可导出的对比数据")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出对比图表",
            f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG图片 (*.png);;PDF文档 (*.pdf);;SVG矢量图 (*.svg)"
        )
        
        if filename:
            try:
                exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
                exporter.export(filename)
                QMessageBox.information(self, "导出成功", f"图表已导出到:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {str(e)}")
    
    @Slot()
    def _on_export_table(self):
        """导出参数对比表"""
        if self.param_table.rowCount() == 0:
            QMessageBox.warning(self, "无数据", "没有可导出的参数数据")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出参数对比表",
            f"comparison_params_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )
        
        if filename:
            try:
                # 提取表格数据
                data = []
                headers = [
                    self.param_table.horizontalHeaderItem(i).text()
                    for i in range(self.param_table.columnCount())
                ]
                
                for row in range(self.param_table.rowCount()):
                    row_data = [
                        self.param_table.item(row, col).text() if self.param_table.item(row, col) else ""
                        for col in range(self.param_table.columnCount())
                    ]
                    data.append(row_data)
                
                df = pd.DataFrame(data, columns=headers)
                
                if filename.endswith('.xlsx'):
                    df.to_excel(filename, index=False, engine='openpyxl')
                else:
                    df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                QMessageBox.information(self, "导出成功", f"参数表已导出到:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出失败: {str(e)}")

