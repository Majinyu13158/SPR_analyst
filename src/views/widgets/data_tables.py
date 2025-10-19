# -*- coding: utf-8 -*-
"""
数据表格组件 - 从旧版本迁移

原始文件: spr_gui_main.py - Custom_TableWidget系列
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHeaderView, QTableWidget
from PySide6.QtCore import Qt
import pandas as pd


class BaseTableWidget(QTableWidget):
    """
    基础表格组件
    
    提供通用的表格功能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_base()
    
    def _setup_base(self):
        """设置基础属性"""
        # 外观设置
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        
        # ⭐ 需求3.2：支持单元格编辑（双击编辑）
        self.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        
        # 列宽策略：默认随容器伸展填满空间（后续可手动调整某列）
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setStretchLastSection(True)
        
        # 允许行高调整（可选）
        self.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        # 样式
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e5e5;
                border-radius: 4px;
                background: #ffffff;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 4px 6px;
            }
            QTableWidget::item:selected {
                background: #e6e6e6;
                color: #000000;
            }
            QTableWidget::item:alternate {
                background: #fafafa;
            }
            QHeaderView::section {
                background: #f7f7f7;
                padding: 6px 8px;
                border: none;
                border-right: 1px solid #ececec;
                border-bottom: 1px solid #ececec;
                font-weight: 600;
            }
        """)


class DataTableWidget(BaseTableWidget):
    """
    数据表格 - 显示实验数据
    
    从旧版本迁移: Custom_TableWidget_Data
    
    列：ID, Time, XValue, YValue, YPrediction
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_columns()
    
    def _setup_columns(self):
        """设置列"""
        headers = ['ID', '时间(s)', 'X值', 'Y值', 'Y预测']
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        self.setColumnWidth(0, 80)   # ID
        self.setColumnWidth(1, 100)  # Time
        self.setColumnWidth(2, 100)  # XValue
        self.setColumnWidth(3, 100)  # YValue
        self.setColumnWidth(4, 100)  # YPrediction
    
    def load_data(self, data):
        """
        加载数据到表格
        
        参数:
            data: DataFrame 或 JSON字典，包含数据
        """
        self.setRowCount(0)  # 清空现有数据
        
        # 支持两种输入格式
        if isinstance(data, dict):
            # 原项目格式：JSON字典 - 参考spr_gui_main.py的data_in_from_json方法
            self.data_in_from_json(data)
        elif isinstance(data, pd.DataFrame):
            # DataFrame格式
            self._load_from_dataframe(data)
    
    def data_in_from_json(self, data: dict):
        """
        从JSON字典加载数据（完全参考原项目spr_gui_main.py第820-836行）
        
        参数:
            data: JSON字典，包含CalculateDataList
        """
        if 'CalculateDataList' in data:
            self.fillTable(data['CalculateDataList'])
        else:
            print("[DataTableWidget] 警告：JSON中没有CalculateDataList")
    
    def fillTable(self, dataList: list, startRow: int = 0):
        """
        填充表格（完全参考原项目spr_gui_main.py第823-828行）
        
        参数:
            dataList: CalculateDataList数组
            startRow: 起始行
        """
        current_row = startRow
        
        for i, dataPoint in enumerate(dataList):
            # 提取BaseData
            baseData = dataPoint.get('BaseData', [])
            if baseData:
                self.fillSubTable(baseData, current_row)
                current_row += len(baseData)
            
            # 提取CombineData
            combineData = dataPoint.get('CombineData', [])
            if combineData:
                self.fillSubTable(combineData, current_row)
                current_row += len(combineData)
            
            # 可选：提取DissociationData
            dissociationData = dataPoint.get('DissociationData', [])
            if dissociationData:
                self.fillSubTable(dissociationData, current_row)
                current_row += len(dissociationData)
        
        # ⭐ 隐藏Time列（列1），只显示XValue列
        # 用户说：x列就是time列，不需要同时显示两列
        self.setColumnHidden(1, True)
        
        print(f"[DataTableWidget] 填充完成：共 {current_row} 行数据（Time列已隐藏）")
    
    def fillSubTable(self, subDataList: list, startRow: int):
        """
        填充子表格（完全参考原项目spr_gui_main.py第830-836行）
        
        参数:
            subDataList: BaseData、CombineData或DissociationData数组
            startRow: 起始行
        """
        for i, dataPoint in enumerate(subDataList):
            rowPosition = startRow + i
            self.insertRow(rowPosition)
            
            # 列0: ID
            id_value = dataPoint.get('ID', 'N/A')
            self.setItem(rowPosition, 0, self._create_item(str(id_value)))
            
            # 列1: Time（可能为None）
            time_value = dataPoint.get('Time')
            if time_value is not None:
                self.setItem(rowPosition, 1, self._create_item(f"{time_value:.3f}"))
            else:
                self.setItem(rowPosition, 1, self._create_item('N/A'))
            
            # 列2: XValue
            x_value = dataPoint.get('XValue', 'N/A')
            if isinstance(x_value, (int, float)):
                self.setItem(rowPosition, 2, self._create_item(f"{x_value:.6f}"))
            else:
                self.setItem(rowPosition, 2, self._create_item(str(x_value)))
            
            # 列3: YValue
            y_value = dataPoint.get('YValue', 'N/A')
            if isinstance(y_value, (int, float)):
                self.setItem(rowPosition, 3, self._create_item(f"{y_value:.6f}"))
            else:
                self.setItem(rowPosition, 3, self._create_item(str(y_value)))
            
            # 列4: YPrediction
            y_pred = dataPoint.get('YPrediction', 0.0)
            if isinstance(y_pred, (int, float)):
                self.setItem(rowPosition, 4, self._create_item(f"{y_pred:.6f}"))
            else:
                self.setItem(rowPosition, 4, self._create_item(str(y_pred)))
    
    def _load_from_dataframe(self, data: pd.DataFrame):
        """
        从DataFrame加载数据（向后兼容）
        
        参数:
            data: DataFrame，包含数据
        """
        if data.empty:
            return
        
        # 设置行数
        row_count = len(data)
        self.setRowCount(row_count)
        
        # 填充数据
        for row_idx, (_, row) in enumerate(data.iterrows()):
            # ID
            if 'ID' in row:
                self.setItem(row_idx, 0, self._create_item(str(row['ID'])))
            
            # Time
            if 'Time' in row:
                time_val = row['Time']
                if pd.notna(time_val):
                    self.setItem(row_idx, 1, self._create_item(f"{time_val:.3f}"))
                else:
                    self.setItem(row_idx, 1, self._create_item('N/A'))
            elif 'XValue' in row:
                self.setItem(row_idx, 1, self._create_item(f"{row['XValue']:.3f}"))
            
            # XValue
            if 'XValue' in row:
                self.setItem(row_idx, 2, self._create_item(f"{row['XValue']:.6f}"))
            
            # YValue
            if 'YValue' in row:
                self.setItem(row_idx, 3, self._create_item(f"{row['YValue']:.6f}"))
            
            # YPrediction
            if 'YPrediction' in row:
                self.setItem(row_idx, 4, self._create_item(f"{row['YPrediction']:.6f}"))
    
    def _create_item(self, text: str):
        """创建表格项"""
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        return item


class ResultTableWidget(BaseTableWidget):
    """
    结果表格 - 显示拟合结果
    
    从旧版本迁移: Custom_TableWidget_Result
    
    列：参数, 值, 误差, 单位
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_columns()
    
    def _setup_columns(self):
        """设置列"""
        headers = ['参数', '值', '误差', '单位']
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        self.setColumnWidth(0, 150)  # 参数名
        self.setColumnWidth(1, 150)  # 值
        self.setColumnWidth(2, 100)  # 误差
        self.setColumnWidth(3, 80)   # 单位
    
    def load_result(self, result_dict: dict):
        """
        加载拟合结果
        
        参数:
            result_dict: 结果字典，如 {'Rmax': (1.5, 0.01, 'RU'), ...}
        """
        self.setRowCount(0)
        
        if not result_dict:
            return
        
        # 设置行数
        self.setRowCount(len(result_dict))
        
        # 填充数据
        for row_idx, (param_name, value_tuple) in enumerate(result_dict.items()):
            # 参数名
            self.setItem(row_idx, 0, self._create_item(param_name))
            
            # 处理不同格式的值
            if isinstance(value_tuple, (list, tuple)):
                # (value, error, unit) 格式
                if len(value_tuple) >= 1:
                    self.setItem(row_idx, 1, self._create_item(f"{value_tuple[0]:.6e}"))
                if len(value_tuple) >= 2:
                    self.setItem(row_idx, 2, self._create_item(f"{value_tuple[1]:.6e}"))
                if len(value_tuple) >= 3:
                    self.setItem(row_idx, 3, self._create_item(str(value_tuple[2])))
            else:
                # 单个值
                self.setItem(row_idx, 1, self._create_item(f"{value_tuple:.6e}"))
    
    def _create_item(self, text: str):
        """创建表格项"""
        from PySide6.QtWidgets import QTableWidgetItem
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        return item


class ProjectDetailTableWidget(BaseTableWidget):
    """
    项目详情表格 - 显示项目元信息
    
    从旧版本迁移: Custom_TableWidget_ProjectDetail
    
    格式：两列 (属性, 值)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_columns()
        self._init_rows()
    
    def _setup_columns(self):
        """设置列"""
        headers = ['属性', '值']
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 设置列宽
        self.setColumnWidth(0, 150)  # 属性名
        self.horizontalHeader().setStretchLastSection(True)
    
    def _init_rows(self):
        """初始化行"""
        attributes = [
            '实验编号',
            '实验时间',
            '所属项目',
            '实验人员',
            '实验地点',
            '实验仪器',
            '实验方法',
            '实验样品',
            '实验目的'
        ]
        
        self.setRowCount(len(attributes))
        
        for row_idx, attr in enumerate(attributes):
            self.setItem(row_idx, 0, self._create_item(attr, bold=True))
            self.setItem(row_idx, 1, self._create_item(''))
    
    def load_details(self, details: dict):
        """
        加载项目详情
        
        参数:
            details: 详情字典
        """
        # 映射关系
        mapping = {
            '实验编号': 'ExperimentID',
            '实验时间': 'ExperimentTime',
            '所属项目': 'Project',
            '实验人员': 'Operator',
            '实验地点': 'Location',
            '实验仪器': 'Instrument',
            '实验方法': 'Method',
            '实验样品': 'Sample',
            '实验目的': 'Purpose'
        }
        
        for row_idx in range(self.rowCount()):
            attr_item = self.item(row_idx, 0)
            if attr_item:
                attr_name = attr_item.text()
                key = mapping.get(attr_name)
                if key and key in details:
                    value = str(details[key])
                    self.setItem(row_idx, 1, self._create_item(value))
    
    def _create_item(self, text: str, bold: bool = False):
        """创建表格项"""
        from PySide6.QtWidgets import QTableWidgetItem
        from PySide6.QtGui import QFont
        
        item = QTableWidgetItem(text)
        
        if bold:
            font = QFont()
            font.setBold(True)
            item.setFont(font)
            item.setTextAlignment(Qt.AlignCenter)
        else:
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        return item

