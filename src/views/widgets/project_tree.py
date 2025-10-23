# -*- coding: utf-8 -*-
"""
项目导航树组件 - 完全重构版

功能：
1. 四大分类：数据、图形、结果、项目详情
2. 每个分类下有"点击新建"节点
3. 点击"点击新建"后立即创建新节点
4. 支持右键菜单（删除、重命名）
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QMenu, QInputDialog, QLineEdit, QComboBox, QPushButton
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction


class ProjectTreeWidget(QWidget):
    """
    项目导航树组件
    
    信号：
        item_clicked: (item_type: str, item_id: int) 节点被点击
        new_item_created: (item_type: str, item_name: str) 新节点创建
        create_figure_from_data: (data_id: int) 从数据创建图表
        fit_data_requested: (data_id: int) 请求拟合数据
        change_figure_source: (figure_id: int) 更改图表数据源
        view_linked_data: (item_type: str, item_id: int) 查看关联数据
        export_item: (item_type: str, item_id: int) 导出项目
    """
    
    # 信号定义
    item_clicked = Signal(str, int)
    new_item_created = Signal(str, str)
    create_figure_from_data = Signal(int)  # data_id
    fit_data_requested = Signal(int)  # data_id
    batch_fit_requested = Signal(list)  # [data_id1, data_id2, ...]
    change_figure_source = Signal(int)  # figure_id
    view_linked_data = Signal(str, int)  # item_type, item_id
    export_item = Signal(str, int)  # item_type, item_id
    add_to_comparison = Signal(list)  # [data_id1, data_id2, ...] 添加到对比
    edit_figure_style = Signal(int)  # figure_id 编辑图表样式
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 计数器：用于生成默认名称
        self._counters = {
            'data': 0,
            'figure': 0,
            'result': 0,
            'project': 0
        }
        
        # 存储节点映射
        self._item_map = {}  # TreeWidgetItem -> (type, id)
        self._new_item_buttons = {}  # type -> "点击新建"节点
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ========== 搜索栏 ==========
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 5, 5, 5)
        
        # 搜索图标标签
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索项目...")
        self.search_input.setClearButtonEnabled(True)  # 显示清除按钮
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input, 1)
        
        # 类型筛选下拉框
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "数据", "图表", "结果"])
        self.filter_combo.setCurrentIndex(0)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        search_layout.addWidget(self.filter_combo)
        
        # 匹配数量标签
        self.match_label = QLabel("")
        self.match_label.setStyleSheet("color: #666; font-size: 11px;")
        search_layout.addWidget(self.match_label)
        
        layout.addLayout(search_layout)
        
        # 树形控件
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        # ⭐ 支持多选（Ctrl/Shift选择多个节点）
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        # 避免初始焦点绘制高亮（蓝色）
        self.tree.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.tree)
        
        # 初始化树结构
        self._init_tree_structure()
        
        # 应用样式
        self.tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background: #ffffff;
                outline: 0; /* 移除控件外轮廓 */
            }
            QTreeWidget::item {
                height: 28px;
                padding: 4px 6px;
                color: #000000;
            }
            QTreeWidget::item:hover {
                background: #f2f2f2;
            }
            /* 选中态：灰底黑字，无边框/阴影/金属感 */
            QTreeWidget::item:selected,
            QTreeWidget::item:selected:active,
            QTreeWidget::item:selected:!active {
                background: #e6e6e6;
                color: #000000;
                border: none;
                outline: 0;
            }
        """)
    
    def _init_tree_structure(self):
        """初始化树形结构"""
        # 根节点
        root = QTreeWidgetItem()
        root.setText(0, "项目导航")
        self.tree.addTopLevelItem(root)
        root.setExpanded(True)
        # 使根节点不可选中，且清除任何初始选中状态，避免启动时出现选中色
        root.setSelected(False)
        root.setFlags(root.flags() & ~Qt.ItemIsSelectable)
        self.tree.clearSelection()
        
        # 四大分类节点
        self.data_root = QTreeWidgetItem(root)
        self.data_root.setText(0, "数据")
        self.data_root.setExpanded(True)
        
        self.figure_root = QTreeWidgetItem(root)
        self.figure_root.setText(0, "图形")
        self.figure_root.setExpanded(True)
        
        self.result_root = QTreeWidgetItem(root)
        self.result_root.setText(0, "结果")
        self.result_root.setExpanded(True)
        
        self.project_root = QTreeWidgetItem(root)
        self.project_root.setText(0, "项目详情")
        self.project_root.setExpanded(True)
        
        # 为每个分类添加"点击新建"节点
        self._add_new_item_button(self.data_root, 'data')
        self._add_new_item_button(self.figure_root, 'figure')
        self._add_new_item_button(self.result_root, 'result')
        self._add_new_item_button(self.project_root, 'project')

        # 清除任何初始选中/当前项，防止启动时出现蓝色选中背景
        try:
            from PySide6.QtCore import QModelIndex
            self.tree.clearSelection()
            self.tree.setCurrentIndex(QModelIndex())
        except Exception:
            pass
    
    def _add_new_item_button(self, parent: QTreeWidgetItem, item_type: str):
        """添加"点击新建"节点"""
        button_item = QTreeWidgetItem(parent)
        button_item.setText(0, "点击新建")
        # 文本颜色使用默认黑色
        
        # 存储按钮节点
        self._new_item_buttons[item_type] = button_item
        self._item_map[button_item] = ('new_button', item_type)
    
    def _connect_signals(self):
        """连接信号"""
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """处理节点点击"""
        if item not in self._item_map:
            return
        
        item_type, item_data = self._item_map[item]
        
        # 如果是"点击新建"按钮
        if item_type == 'new_button':
            category = item_data
            self._create_new_item(category)
        # 如果是普通节点
        else:
            item_id = item_data
            self.item_clicked.emit(item_type, item_id)
    
    def _create_new_item(self, category: str):
        """
        创建新节点（⭐需求2修复：不在这里创建树节点，避免重复）
        
        修改前：在这里创建树节点 + 发射信号 → Controller创建Data → 导致重复
        修改后：只发射信号 → Controller创建Data → Controller添加树节点
        """
        # 增加计数器
        self._counters[category] += 1
        count = self._counters[category]
        
        # 生成默认名称
        name_map = {
            'data': f"数据{count}",
            'figure': f"图形{count}",
            'result': f"结果{count}",
            'project': f"项目{count}"
        }
        default_name = name_map[category]
        
        # ⭐ 只发射信号，不创建节点
        # Controller会在创建Data对象后调用add_data_item添加节点
        self.new_item_created.emit(category, default_name)
        
        print(f"[ProjectTreeWidget] 请求创建新{category}: {default_name}")
    
    def _on_context_menu(self, position):
        """显示右键菜单（增强版，根据节点类型显示不同菜单）"""
        item = self.tree.itemAt(position)
        if not item or item not in self._item_map:
            return
        
        item_type, item_id = self._item_map[item]
        
        # "点击新建"按钮不显示右键菜单
        if item_type == 'new_button':
            return
        
        # 根节点和分类节点不显示右键菜单
        if item in [self.data_root, self.figure_root, self.result_root, self.project_root]:
            return
        
        # 创建右键菜单
        menu = QMenu(self)
        
        # ⭐ 检查是否多选数据节点
        selected_items = self.tree.selectedItems()
        selected_data_ids = []
        for selected_item in selected_items:
            if selected_item in self._item_map:
                sel_type, sel_id = self._item_map[selected_item]
                if sel_type == 'data':
                    selected_data_ids.append(sel_id)
        
        # ========== 多选数据节点菜单 ==========
        if len(selected_data_ids) > 1:
            # 批量拟合
            batch_fit_action = QAction(f"批量拟合 ({len(selected_data_ids)}个数据)...", self)
            batch_fit_action.triggered.connect(
                lambda: self._on_batch_fit_requested(selected_data_ids)
            )
            menu.addAction(batch_fit_action)
            
            # ⭐ 添加到对比
            add_comparison_action = QAction(f"📊 添加到对比 ({len(selected_data_ids)}个数据)", self)
            add_comparison_action.triggered.connect(
                lambda: self.add_to_comparison.emit(selected_data_ids)
            )
            menu.addAction(add_comparison_action)
            
            menu.addSeparator()
            
            # 批量导出（未来功能）
            # batch_export_action = QAction(f"批量导出 ({len(selected_data_ids)}个数据)...", self)
            # menu.addAction(batch_export_action)
            
            # 显示菜单
            menu.exec(self.tree.viewport().mapToGlobal(position))
            return
        
        # ========== 单选数据节点特定菜单 ==========
        if item_type == 'data':
            # 创建图表
            create_figure_action = QAction("创建图表", self)
            create_figure_action.triggered.connect(
                lambda: self.create_figure_from_data.emit(item_id)
            )
            menu.addAction(create_figure_action)
            
            # 拟合分析
            fit_action = QAction("拟合分析", self)
            fit_action.triggered.connect(
                lambda: self.fit_data_requested.emit(item_id)
            )
            menu.addAction(fit_action)
            
            menu.addSeparator()
            
            # ⭐ 添加到对比
            add_comparison_action = QAction("📊 添加到对比", self)
            add_comparison_action.triggered.connect(
                lambda: self.add_to_comparison.emit([item_id])
            )
            menu.addAction(add_comparison_action)
            
            menu.addSeparator()
            
            # 导出数据
            export_data_action = QAction("导出数据...", self)
            export_data_action.triggered.connect(
                lambda: self.export_item.emit(item_type, item_id)
            )
            menu.addAction(export_data_action)
            
            # 查看关联对象
            view_linked_action = QAction("查看关联对象", self)
            view_linked_action.triggered.connect(
                lambda: self.view_linked_data.emit(item_type, item_id)
            )
            menu.addAction(view_linked_action)
        
        # ========== 图表节点特定菜单 ==========
        elif item_type == 'figure':
            # 编辑样式
            style_action = QAction("🎨 编辑样式", self)
            style_action.triggered.connect(
                lambda: self.edit_figure_style.emit(item_id)
            )
            menu.addAction(style_action)
            
            menu.addSeparator()
            
            # 更改数据源
            change_source_action = QAction("更改数据源", self)
            change_source_action.triggered.connect(
                lambda: self.change_figure_source.emit(item_id)
            )
            menu.addAction(change_source_action)
            
            # 查看关联对象
            view_linked_action = QAction("查看关联对象", self)
            view_linked_action.triggered.connect(
                lambda: self.view_linked_data.emit(item_type, item_id)
            )
            menu.addAction(view_linked_action)
            
            menu.addSeparator()
            
            # 导出图像
            export_action = QAction("导出图像", self)
            export_action.triggered.connect(
                lambda: self.export_item.emit(item_type, item_id)
            )
            menu.addAction(export_action)
        
        # ========== 结果节点特定菜单 ==========
        elif item_type == 'result':
            # 查看源数据
            view_source_action = QAction("查看源数据", self)
            view_source_action.triggered.connect(
                lambda: self.view_linked_data.emit(item_type, item_id)
            )
            menu.addAction(view_source_action)
            
            # 查看拟合曲线
            view_curve_action = QAction("查看拟合曲线", self)
            view_curve_action.triggered.connect(
                lambda: self._view_fit_curve(item_id)
            )
            menu.addAction(view_curve_action)
            
            menu.addSeparator()
            
            # 导出结果
            export_action = QAction("导出结果", self)
            export_action.triggered.connect(
                lambda: self.export_item.emit(item_type, item_id)
            )
            menu.addAction(export_action)
        
        # ========== 项目节点特定菜单 ==========
        elif item_type == 'project':
            # 查看项目详情
            view_details_action = QAction("查看详情", self)
            view_details_action.triggered.connect(
                lambda: self.item_clicked.emit(item_type, item_id)
            )
            menu.addAction(view_details_action)
            
            menu.addSeparator()
        
        # ========== 通用菜单 ==========
        menu.addSeparator()
        
        # 重命名
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self._rename_item(item))
        menu.addAction(rename_action)
        
        # 删除
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self._delete_item(item))
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec(self.tree.viewport().mapToGlobal(position))
    
    def _view_fit_curve(self, result_id: int):
        """查看拟合曲线（内部方法）"""
        # 通过view_linked_data信号通知Controller
        self.view_linked_data.emit('result', result_id)
    
    def _rename_item(self, item: QTreeWidgetItem):
        """重命名节点"""
        current_text = item.text(0)
        current_name = current_text
        
        new_name, ok = QInputDialog.getText(
            self,
            "重命名",
            "输入新名称:",
            text=current_name
        )
        
        if ok and new_name:
            item.setText(0, new_name)
    
    def _delete_item(self, item: QTreeWidgetItem):
        """删除节点"""
        parent = item.parent()
        if parent:
            parent.removeChild(item)
            
            # 从映射中移除
            if item in self._item_map:
                del self._item_map[item]
    
    # ========== 公共接口 ==========
    
    def add_data_item(self, data_id: int, name: str, parent_item=None):
        """
        添加数据节点（由Controller调用）
        
        参数:
            data_id: 数据ID
            name: 节点名称
            parent_item: 父节点（可选），如果提供则作为子节点添加
        """
        item = QTreeWidgetItem()
        item.setText(0, f"{name}")
        
        if parent_item is not None:
            # 添加为子节点
            parent_item.addChild(item)
        else:
            # 插入到"点击新建"按钮之前
            insert_index = self.data_root.childCount() - 1
            self.data_root.insertChild(insert_index, item)
        
        self._item_map[item] = ('data', data_id)
        return item  # 返回创建的节点，方便后续操作
    
    def add_data_group(self, group_name: str):
        """
        添加数据组节点（⭐需求1：多样本分组）
        
        参数:
            group_name: 组名称（通常是文件名）
            
        返回:
            group_item: 组节点，可用于添加子节点
        """
        group_item = QTreeWidgetItem()
        group_item.setText(0, f"{group_name}")
        group_item.setExpanded(True)  # 默认展开
        
        # 插入到"点击新建"按钮之前
        insert_index = self.data_root.childCount() - 1
        self.data_root.insertChild(insert_index, group_item)
        
        # 组节点不需要添加到_item_map（不可点击选择数据）
        self._item_map[group_item] = ('data_group', group_name)
        
        return group_item
    
    def add_figure_item(self, figure_id: int, name: str):
        """添加图形节点"""
        item = QTreeWidgetItem()
        item.setText(0, f"{name}")
        
        insert_index = self.figure_root.childCount() - 1
        self.figure_root.insertChild(insert_index, item)
        
        self._item_map[item] = ('figure', figure_id)
    
    def add_result_item(self, result_id: int, name: str):
        """添加结果节点"""
        item = QTreeWidgetItem()
        item.setText(0, f"{name}")
        
        insert_index = self.result_root.childCount() - 1
        self.result_root.insertChild(insert_index, item)
        
        self._item_map[item] = ('result', result_id)
    
    def add_project_item(self, project_id: int, name: str):
        """添加项目节点"""
        item = QTreeWidgetItem()
        item.setText(0, f"{name}")
        
        insert_index = self.project_root.childCount() - 1
        self.project_root.insertChild(insert_index, item)
        
        self._item_map[item] = ('project', project_id)
    
    def _on_batch_fit_requested(self, data_ids: list):
        """
        处理批量拟合请求
        
        参数:
            data_ids: 数据ID列表
        """
        print(f"[ProjectTreeWidget] 批量拟合请求: {len(data_ids)}个数据")
        self.batch_fit_requested.emit(data_ids)
    
    def clear_all(self):
        """清空所有节点（保留"点击新建"）"""
        for parent in [self.data_root, self.figure_root, self.result_root, self.project_root]:
            # 移除除最后一个（"点击新建"）外的所有子节点
            while parent.childCount() > 1:
                child = parent.child(0)
                parent.removeChild(child)
                if child in self._item_map:
                    del self._item_map[child]
        
        # 重置计数器
        for key in self._counters:
            self._counters[key] = 0
    
    def highlight_item(self, item_type: str, item_id: int):
        """
        高亮并跳转到指定节点
        
        参数:
            item_type: 节点类型（data/figure/result/project）
            item_id: 节点ID
        """
        # 查找匹配的节点
        for item, (i_type, i_id) in self._item_map.items():
            if i_type == item_type and i_id == item_id:
                # 设置为当前选中项
                self.tree.setCurrentItem(item)
                # 滚动到可见区域
                self.tree.scrollToItem(item)
                # 展开父节点
                if item.parent():
                    item.parent().setExpanded(True)
                # 设置焦点
                self.tree.setFocus()
                print(f"[ProjectTreeWidget] 高亮节点: {item_type}:{item_id}")
                return True
        
        print(f"[ProjectTreeWidget] 警告: 未找到节点 {item_type}:{item_id}")
        return False
    
    # ========== 搜索/过滤功能 ==========
    
    def _on_search_text_changed(self, text: str):
        """搜索文本变化时"""
        self._apply_filter()
    
    def _on_filter_changed(self, index: int):
        """类型筛选变化时"""
        self._apply_filter()
    
    def _apply_filter(self):
        """应用搜索和过滤"""
        search_text = self.search_input.text().strip().lower()
        filter_type = self.filter_combo.currentText()
        
        # 计数器
        match_count = 0
        total_count = 0
        
        # 遍历所有分类根节点
        type_map = {
            "数据": self.data_root,
            "图表": self.figure_root,
            "结果": self.result_root
        }
        
        for type_name, root in type_map.items():
            # 如果类型筛选不匹配，隐藏整个分类
            if filter_type != "全部" and filter_type != type_name:
                root.setHidden(True)
                continue
            else:
                root.setHidden(False)
            
            # 遍历该分类下的所有子节点
            for i in range(root.childCount()):
                item = root.child(i)
                item_text = item.text(0).lower()
                
                # 跳过"点击新建"节点
                if "点击新建" in item_text or "click to create" in item_text:
                    item.setHidden(False)
                    continue
                
                total_count += 1
                
                # 判断是否匹配搜索文本
                if not search_text or search_text in item_text:
                    # 匹配，显示
                    item.setHidden(False)
                    match_count += 1
                    
                    # 递归显示子节点
                    self._show_all_children(item)
                else:
                    # 不匹配，隐藏
                    item.setHidden(True)
        
        # 更新匹配数量标签
        if search_text or filter_type != "全部":
            self.match_label.setText(f"显示 {match_count}/{total_count} 项")
        else:
            self.match_label.setText("")
    
    def _show_all_children(self, item: QTreeWidgetItem):
        """递归显示所有子节点"""
        for i in range(item.childCount()):
            child = item.child(i)
            child.setHidden(False)
            self._show_all_children(child)
    
    def focus_search(self):
        """聚焦到搜索框（用于快捷键Ctrl+F）"""
        self.search_input.setFocus()
        self.search_input.selectAll()
