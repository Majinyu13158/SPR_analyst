# -*- coding: utf-8 -*-
"""
SeriesTreeWidget - 系列树控件

功能：
- 显示系列与其包含的数据
- 新建/重命名/删除系列
- 将数据添加/移除到系列（后续可支持拖拽）
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction


class SeriesTreeWidget(QWidget):
    series_create_requested = Signal(str)      # name
    series_rename_requested = Signal(int, str)
    series_delete_requested = Signal(int)
    series_add_data_requested = Signal(int)    # series_id
    series_remove_data_requested = Signal(int, int)  # series_id, data_id
    series_selected = Signal(int)              # series_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._series_items = {}  # QTreeWidgetItem -> ('series', id) or ('data', series_id, data_id)
        self._series_root = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context)
        self.tree.itemClicked.connect(self._on_clicked)
        layout.addWidget(self.tree)

        # root
        root = QTreeWidgetItem()
        root.setText(0, "系列")
        self.tree.addTopLevelItem(root)
        root.setExpanded(True)
        self._series_root = root

        # 样式
        self.tree.setStyleSheet("""
            QTreeWidget { border:none; background:#ffffff; }
            QTreeWidget::item { height:26px; padding:3px 6px; color:#000; }
            QTreeWidget::item:hover { background:#f2f2f2; }
            QTreeWidget::item:selected { background:#e6e6e6; color:#000; }
        """)

    def _on_clicked(self, item: QTreeWidgetItem, column: int):
        info = self._series_items.get(item)
        if not info:
            return
        if info[0] == 'series':
            self.series_selected.emit(info[1])

    def _on_context(self, pos):
        item = self.tree.itemAt(pos)
        menu = QMenu(self)
        if not item or item not in self._series_items:
            # root 空白处：新建
            act_new = QAction("新建系列", self)
            act_new.triggered.connect(self._create_series_dialog)
            menu.addAction(act_new)
            menu.exec(self.tree.viewport().mapToGlobal(pos))
            return

        info = self._series_items[item]
        if info[0] == 'series':
            sid = info[1]
            act_new = QAction("新建系列", self)
            act_new.triggered.connect(self._create_series_dialog)
            menu.addAction(act_new)
            act_rename = QAction("重命名", self)
            act_rename.triggered.connect(lambda: self._rename_series_dialog(sid, item.text(0)))
            menu.addAction(act_rename)
            act_del = QAction("删除系列", self)
            act_del.triggered.connect(lambda: self.series_delete_requested.emit(sid))
            menu.addAction(act_del)
            menu.addSeparator()
            act_add_data = QAction("添加数据到系列", self)
            act_add_data.triggered.connect(lambda: self.series_add_data_requested.emit(sid))
            menu.addAction(act_add_data)
        elif info[0] == 'data':
            sid, did = info[1], info[2]
            act_remove = QAction("从系列移除", self)
            act_remove.triggered.connect(lambda: self.series_remove_data_requested.emit(sid, did))
            menu.addAction(act_remove)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _create_series_dialog(self):
        name, ok = QInputDialog.getText(self, "新建系列", "名称：", text="系列1")
        if ok and name:
            self.series_create_requested.emit(name)

    def _rename_series_dialog(self, sid: int, old: str):
        name, ok = QInputDialog.getText(self, "重命名系列", "名称：", text=old)
        if ok and name:
            self.series_rename_requested.emit(sid, name)

    # ---------- Public API ----------
    def add_series_item(self, series_id: int, name: str):
        item = QTreeWidgetItem(self._series_root)
        item.setText(0, name)
        item.setExpanded(True)
        self._series_items[item] = ('series', series_id)
        return item

    def add_series_data_item(self, parent_series_item: QTreeWidgetItem, series_id: int, data_id: int, data_name: str):
        child = QTreeWidgetItem(parent_series_item)
        child.setText(0, data_name)
        self._series_items[child] = ('data', series_id, data_id)
        return child

    def rename_series_item(self, series_item: QTreeWidgetItem, new_name: str):
        series_item.setText(0, new_name)


