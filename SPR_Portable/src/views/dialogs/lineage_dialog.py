# -*- coding: utf-8 -*-
"""
数据血缘可视化对话框

功能：
1. 以图形方式展示数据、操作、结果之间的关系
2. 支持点击节点查看详情
3. 支持导出为PNG图片
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
    QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem,
    QFileDialog, QMessageBox, QGraphicsItem, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QCursor
from typing import Dict, List, Tuple, Optional


class LineageNode:
    """血缘图节点"""
    
    def __init__(self, node_id: str, node_type: str, label: str):
        """
        参数:
            node_id: 节点ID（如 "data:1", "result:2"）
            node_type: 节点类型（data/figure/result/operation/file）
            label: 显示标签
        """
        self.node_id = node_id
        self.node_type = node_type
        self.label = label
        self.x = 0.0
        self.y = 0.0
        self.width = 150.0
        self.height = 60.0
        
        # 根据类型设置颜色
        self.color = self._get_color_by_type(node_type)
    
    def _get_color_by_type(self, node_type: str) -> QColor:
        """根据类型返回颜色"""
        color_map = {
            'file': QColor(232, 244, 253),      # 浅蓝
            'data': QColor(212, 233, 247),      # 蓝
            'operation': QColor(255, 244, 204), # 黄
            'result': QColor(213, 245, 227),    # 绿
            'figure': QColor(252, 228, 236)     # 粉
        }
        return color_map.get(node_type, QColor(240, 240, 240))
    
    def get_center(self) -> QPointF:
        """返回节点中心点"""
        return QPointF(self.x + self.width / 2, self.y + self.height / 2)


class LineageEdge:
    """血缘图边"""
    
    def __init__(self, from_node: str, to_node: str, label: str = ""):
        """
        参数:
            from_node: 源节点ID
            to_node: 目标节点ID
            label: 边标签（操作类型）
        """
        self.from_node = from_node
        self.to_node = to_node
        self.label = label


class ClickableNodeItem(QGraphicsRectItem):
    """可点击的节点图形项"""
    
    def __init__(self, node: LineageNode, dialog):
        super().__init__(node.x, node.y, node.width, node.height)
        self.node = node
        self.dialog = dialog
        self.original_color = node.color
        
        # 设置外观
        self.setBrush(QBrush(node.color))
        self.setPen(QPen(QColor(200, 200, 200), 1.5))
        self.setZValue(2)
        
        # 设置圆角
        # Note: QGraphicsRectItem 不直接支持圆角，但边框足够
        
        # 启用交互
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # 设置tooltip
        self.setToolTip(f"点击查看: {node.label}\n类型: {node.node_type}")
        
        # ⭐ 添加现代阴影效果（仅在悬停时显示）
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.shadow.setOffset(0, 3)
        self.shadow.setEnabled(False)  # 默认禁用
        self.setGraphicsEffect(self.shadow)
    
    def hoverEnterEvent(self, event):
        """鼠标进入 - 显示阴影"""
        self.shadow.setEnabled(True)
        self.setZValue(3)  # 提升层级
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """鼠标离开 - 隐藏阴影"""
        self.shadow.setEnabled(False)
        self.setZValue(2)  # 恢复层级
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标点击 - 发射信号（不关闭对话框）"""
        if event.button() == Qt.LeftButton:
            # 发射信号到对话框
            self.dialog.node_clicked.emit(self.node.node_id)
            # ⭐ 不再关闭对话框，保持打开状态
        super().mousePressEvent(event)


class LineageDialog(QDialog):
    """
    数据血缘可视化对话框
    
    显示数据、操作、结果之间的关系图
    """
    
    # ⭐ 信号：节点被点击 (node_id: "data:5", "figure:3", etc.)
    node_clicked = Signal(str)
    
    def __init__(self, link_manager, data_manager, result_manager, 
                 figure_manager, provenance_manager, parent=None):
        super().__init__(parent)
        
        self.link_manager = link_manager
        self.data_manager = data_manager
        self.result_manager = result_manager
        self.figure_manager = figure_manager
        self.provenance_manager = provenance_manager
        
        self.nodes: Dict[str, LineageNode] = {}
        self.edges: List[LineageEdge] = []
        
        self._setup_ui()
        self._build_graph()
        self._layout_graph()
        self._render_graph()
        
        # ⭐ 连接管理器信号以实现实时更新
        self._connect_manager_signals()
    
    def _setup_ui(self):
        """设置UI"""
        self.setWindowTitle("数据血缘图")
        self.resize(1000, 700)
        
        layout = QVBoxLayout(self)
        
        # 图形视图
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setRenderHint(QPainter.TextAntialiasing)
        self.view.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # ⭐ 启用拖拽模式
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        
        # ⭐ 启用交互式缩放
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # ⭐ 启用滚轮缩放
        self.view.wheelEvent = self._wheel_zoom
        
        layout.addWidget(self.view)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        # 缩放按钮
        zoom_in_btn = QPushButton("放大 (+)")
        zoom_in_btn.clicked.connect(lambda: self.view.scale(1.2, 1.2))
        button_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("缩小 (-)")
        zoom_out_btn.clicked.connect(lambda: self.view.scale(1/1.2, 1/1.2))
        button_layout.addWidget(zoom_out_btn)
        
        zoom_fit_btn = QPushButton("适应窗口")
        zoom_fit_btn.clicked.connect(lambda: self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio))
        button_layout.addWidget(zoom_fit_btn)
        
        button_layout.addSpacing(20)
        
        export_btn = QPushButton("导出PNG")
        export_btn.clicked.connect(self._export_png)
        button_layout.addWidget(export_btn)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _build_graph(self):
        """构建图形数据结构"""
        # 添加所有数据节点
        for data_id, data in self.data_manager.get_all_data().items():
            node_id = f"data:{data_id}"
            # 使用换行文本，限制总长度为40
            wrapped_name = self._wrap_text(data.name[:40], max_width=20)
            node = LineageNode(node_id, 'data', wrapped_name)
            # 根据行数调整高度
            line_count = wrapped_name.count('\n') + 1
            node.height = 40 + line_count * 15
            self.nodes[node_id] = node
        
        # 添加所有结果节点 (返回列表)
        for result in self.result_manager.get_all_results():
            node_id = f"result:{result.id}"
            wrapped_name = self._wrap_text(result.name[:40], max_width=20)
            node = LineageNode(node_id, 'result', wrapped_name)
            line_count = wrapped_name.count('\n') + 1
            node.height = 40 + line_count * 15
            self.nodes[node_id] = node
        
        # 添加所有图表节点 (返回列表)
        for figure in self.figure_manager.get_all_figures():
            node_id = f"figure:{figure.id}"
            wrapped_name = self._wrap_text(figure.name[:40], max_width=20)
            node = LineageNode(node_id, 'figure', wrapped_name)
            line_count = wrapped_name.count('\n') + 1
            node.height = 40 + line_count * 15
            self.nodes[node_id] = node
        
        # 从LinkManager读取所有链接
        all_links = self.link_manager.get_all_links()
        
        for link_data in all_links:
            source_type = link_data['source_type']
            source_id = link_data['source_id']
            target_type = link_data['target_type']
            target_id = link_data['target_id']
            link_type = link_data.get('link_type', '')
            
            from_node = f"{source_type}:{source_id}"
            to_node = f"{target_type}:{target_id}"
            
            # 只添加存在的节点之间的边
            if from_node in self.nodes and to_node in self.nodes:
                self.edges.append(LineageEdge(from_node, to_node, link_type))
        
        print(f"[LineageDialog] 构建图形: {len(self.nodes)}个节点, {len(self.edges)}条边")
    
    def _layout_graph(self):
        """布局算法：简单的层次布局"""
        if not self.nodes:
            return
        
        # 计算每个节点的层级（使用拓扑排序的思想）
        levels: Dict[str, int] = {}
        in_degree: Dict[str, int] = {node_id: 0 for node_id in self.nodes}
        
        # 计算入度
        for edge in self.edges:
            if edge.to_node in in_degree:
                in_degree[edge.to_node] += 1
        
        # 层次布局：从入度为0的节点开始
        current_level = 0
        processed = set()
        
        while len(processed) < len(self.nodes):
            # 找到当前层的节点（入度为0且未处理）
            current_level_nodes = [
                node_id for node_id in self.nodes
                if node_id not in processed and in_degree[node_id] == 0
            ]
            
            if not current_level_nodes:
                # 如果没有入度为0的节点，说明有环或孤立节点
                # 将剩余节点都放到当前层
                current_level_nodes = [
                    node_id for node_id in self.nodes if node_id not in processed
                ]
            
            # 设置层级
            for node_id in current_level_nodes:
                levels[node_id] = current_level
                processed.add(node_id)
                
                # 减少子节点的入度
                for edge in self.edges:
                    if edge.from_node == node_id and edge.to_node in in_degree:
                        in_degree[edge.to_node] -= 1
            
            current_level += 1
        
        # 根据层级设置坐标
        y_spacing = 120  # 层间距
        x_spacing = 200  # 节点间距
        start_x = 50
        start_y = 50
        
        # 按层级分组
        level_groups: Dict[int, List[str]] = {}
        for node_id, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node_id)
        
        # 设置每层节点的位置
        for level, node_ids in level_groups.items():
            y = start_y + level * y_spacing
            total_width = len(node_ids) * x_spacing
            x_offset = start_x
            
            for i, node_id in enumerate(node_ids):
                x = x_offset + i * x_spacing
                self.nodes[node_id].x = x
                self.nodes[node_id].y = y
    
    def _render_graph(self):
        """渲染图形到场景"""
        self.scene.clear()
        
        # 绘制边（先绘制，使其在节点下方）
        for edge in self.edges:
            if edge.from_node in self.nodes and edge.to_node in self.nodes:
                from_node = self.nodes[edge.from_node]
                to_node = self.nodes[edge.to_node]
                
                from_center = from_node.get_center()
                to_center = to_node.get_center()
                
                # 绘制箭头线
                pen = QPen(QColor(100, 100, 100), 2)
                line = self.scene.addLine(
                    from_center.x(), from_center.y(),
                    to_center.x(), to_center.y(),
                    pen
                )
                line.setZValue(0)  # 确保在节点下方
                
                # 添加边标签（如果有）
                if edge.label:
                    mid_x = (from_center.x() + to_center.x()) / 2
                    mid_y = (from_center.y() + to_center.y()) / 2
                    label = self.scene.addText(edge.label)
                    label.setDefaultTextColor(QColor(80, 80, 80))
                    label.setFont(QFont("Arial", 8))
                    label.setPos(mid_x - 20, mid_y - 10)
                    label.setZValue(1)
        
        # 绘制节点 (使用可点击的节点)
        for node in self.nodes.values():
            # ⭐ 使用可点击的节点矩形
            rect = ClickableNodeItem(node, self)
            self.scene.addItem(rect)
            
            # 添加节点标签
            text = self.scene.addText(node.label)
            text.setDefaultTextColor(QColor(0, 0, 0))
            text.setFont(QFont("Arial", 10))
            
            # 居中文本
            text_width = text.boundingRect().width()
            text_height = text.boundingRect().height()
            text.setPos(
                node.x + (node.width - text_width) / 2,
                node.y + (node.height - text_height) / 2
            )
            text.setZValue(3)
            
            # 添加类型标签（小字）
            type_text = self.scene.addText(f"[{node.node_type}]")
            type_text.setDefaultTextColor(QColor(120, 120, 120))
            type_text.setFont(QFont("Arial", 8))
            type_text.setPos(node.x + 5, node.y + 5)
            type_text.setZValue(3)
        
        # 调整视图以适应内容
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def _export_png(self):
        """导出为PNG图片"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出血缘图",
            "lineage_graph.png",
            "PNG图片 (*.png);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            from PySide6.QtGui import QImage
            
            # 创建图像
            rect = self.scene.sceneRect()
            image = QImage(
                int(rect.width()), int(rect.height()),
                QImage.Format_ARGB32
            )
            image.fill(Qt.white)
            
            # 渲染场景到图像
            painter = QPainter(image)
            self.scene.render(painter)
            painter.end()
            
            # 保存图像
            image.save(file_path)
            
            QMessageBox.information(
                self,
                "导出成功",
                f"血缘图已导出到:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "导出失败",
                f"导出失败: {str(e)}"
            )
    
    def _connect_manager_signals(self):
        """连接管理器信号以实现实时更新"""
        # 数据变化
        if hasattr(self.data_manager, 'data_added'):
            self.data_manager.data_added.connect(self._on_data_changed)
        if hasattr(self.data_manager, 'data_removed'):
            self.data_manager.data_removed.connect(self._on_data_changed)
        
        # 结果变化
        if hasattr(self.result_manager, 'result_added'):
            self.result_manager.result_added.connect(self._on_data_changed)
        if hasattr(self.result_manager, 'result_removed'):
            self.result_manager.result_removed.connect(self._on_data_changed)
        
        # 图表变化
        if hasattr(self.figure_manager, 'figure_added'):
            self.figure_manager.figure_added.connect(self._on_data_changed)
        if hasattr(self.figure_manager, 'figure_removed'):
            self.figure_manager.figure_removed.connect(self._on_data_changed)
    
    def _on_data_changed(self, *args):
        """数据变化时自动刷新血缘图"""
        self._refresh()
    
    def _refresh(self):
        """刷新图形"""
        self.nodes.clear()
        self.edges.clear()
        self._build_graph()
        self._layout_graph()
        self._render_graph()
    
    def _wheel_zoom(self, event):
        """滚轮缩放"""
        # 获取滚轮滚动的角度
        angle = event.angleDelta().y()
        
        # 计算缩放因子
        factor = 1.2 if angle > 0 else 1 / 1.2
        
        # 应用缩放
        self.view.scale(factor, factor)
    
    def _wrap_text(self, text: str, max_width: int = 20) -> str:
        """
        文本换行
        
        参数:
            text: 原始文本
            max_width: 最大字符宽度
        
        返回:
            换行后的文本
        """
        if len(text) <= max_width:
            return text
        
        # 简单的换行：在max_width处切断
        lines = []
        while len(text) > max_width:
            lines.append(text[:max_width])
            text = text[max_width:]
        if text:
            lines.append(text)
        
        return '\n'.join(lines)

